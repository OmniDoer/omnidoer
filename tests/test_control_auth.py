import tempfile
import time
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.auth import authenticate_signed_session_request
from omnidoer.omni_control.csrf import verify_csrf
from omnidoer.omni_control.device_signing import DeviceNonceStore, b64url_encode, device_signature_message
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.sessions import SessionStore


def public_jwk(private_key) -> str:
    numbers = private_key.public_key().public_numbers()
    return json.dumps(
        {
            "kty": "EC",
            "crv": "P-256",
            "x": b64url_encode(numbers.x.to_bytes(32, "big")),
            "y": b64url_encode(numbers.y.to_bytes(32, "big")),
        }
    )


def sign_request(private_key, *, device_id: str, session_id: str, method: str = "GET", path: str = "/api/requests", nonce: str = "nonce-1") -> dict[str, str]:
    timestamp = str(int(time.time()))
    message = device_signature_message(
        device_id=device_id,
        session_id=session_id,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
    )
    signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    return {"timestamp": timestamp, "nonce": nonce, "signature": b64url_encode(signature)}


class ControlAuthTest(unittest.TestCase):
    def test_session_token_is_hashed_and_csrf_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SessionStore(Path(tmp) / "sessions.json")
            session, token = store.create(device_id="dev_1")
            raw = Path(tmp, "sessions.json").read_text()
            self.assertNotIn(token, raw)
            self.assertTrue(verify_csrf(session.csrf_token, session.csrf_token))
            self.assertFalse(verify_csrf(session.csrf_token, "wrong"))

    def test_signed_session_request_requires_device_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            devices = DeviceStore(Path(tmp) / "devices.json")
            sessions = SessionStore(Path(tmp) / "sessions.json")
            nonces = DeviceNonceStore(Path(tmp) / "nonces.json")
            key = ec.generate_private_key(ec.SECP256R1())
            device = devices.register(name="Phone", public_key=public_jwk(key))
            session, token = sessions.create(device_id=device.device_id)
            signed = sign_request(key, device_id=device.device_id, session_id=session.session_id)
            authenticated = authenticate_signed_session_request(
                session_id=session.session_id,
                session_token=token,
                device_id=device.device_id,
                method="GET",
                path="/api/requests",
                timestamp=signed["timestamp"],
                nonce=signed["nonce"],
                signature=signed["signature"],
                device_store=devices,
                session_store=sessions,
                nonce_store=nonces,
            )
            self.assertEqual(authenticated.device_id, device.device_id)
            with self.assertRaises(PermissionError):
                authenticate_signed_session_request(
                    session_id=session.session_id,
                    session_token=token,
                    device_id=device.device_id,
                    method="GET",
                    path="/api/requests",
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                    device_store=devices,
                    session_store=sessions,
                    nonce_store=nonces,
                )

    def test_signed_session_request_can_recover_without_session_cookie_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            devices = DeviceStore(Path(tmp) / "devices.json")
            sessions = SessionStore(Path(tmp) / "sessions.json")
            nonces = DeviceNonceStore(Path(tmp) / "nonces.json")
            key = ec.generate_private_key(ec.SECP256R1())
            device = devices.register(name="Phone", public_key=public_jwk(key))
            session, _token = sessions.create(device_id=device.device_id)
            signed = sign_request(key, device_id=device.device_id, session_id=session.session_id)
            authenticated = authenticate_signed_session_request(
                session_id=session.session_id,
                session_token="",
                device_id=device.device_id,
                method="GET",
                path="/api/requests",
                timestamp=signed["timestamp"],
                nonce=signed["nonce"],
                signature=signed["signature"],
                device_store=devices,
                session_store=sessions,
                nonce_store=nonces,
                allow_missing_session_token=True,
            )
            self.assertEqual(authenticated.device_id, device.device_id)
            self.assertIsNotNone(sessions.get(session.session_id).last_seen_at)

    def test_signed_session_request_rejects_wrong_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            devices = DeviceStore(Path(tmp) / "devices.json")
            sessions = SessionStore(Path(tmp) / "sessions.json")
            key = ec.generate_private_key(ec.SECP256R1())
            wrong_key = ec.generate_private_key(ec.SECP256R1())
            device = devices.register(name="Phone", public_key=public_jwk(key))
            session, token = sessions.create(device_id=device.device_id)
            signed = sign_request(wrong_key, device_id=device.device_id, session_id=session.session_id)
            with self.assertRaises(PermissionError):
                authenticate_signed_session_request(
                    session_id=session.session_id,
                    session_token=token,
                    device_id=device.device_id,
                    method="GET",
                    path="/api/requests",
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                    device_store=devices,
                    session_store=sessions,
                )

    def test_concurrent_signed_requests_do_not_corrupt_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            device_path = Path(tmp) / "devices.json"
            session_path = Path(tmp) / "sessions.json"
            nonce_path = Path(tmp) / "nonces.json"
            devices = DeviceStore(device_path)
            sessions = SessionStore(session_path)
            key = ec.generate_private_key(ec.SECP256R1())
            device = devices.register(name="Phone", public_key=public_jwk(key))
            session, token = sessions.create(device_id=device.device_id)
            signed_requests = [
                sign_request(
                    key,
                    device_id=device.device_id,
                    session_id=session.session_id,
                    nonce=f"nonce-{index}",
                )
                for index in range(32)
            ]

            def authenticate(index: int) -> None:
                signed = signed_requests[index]
                authenticate_signed_session_request(
                    session_id=session.session_id,
                    session_token=token,
                    device_id=device.device_id,
                    method="GET",
                    path="/api/requests",
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                    device_store=DeviceStore(device_path),
                    session_store=SessionStore(session_path),
                    nonce_store=DeviceNonceStore(nonce_path),
                )

            with ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(authenticate, range(len(signed_requests))))

            self.assertEqual(len(json.loads(nonce_path.read_text())), len(signed_requests))
            self.assertIn(session.session_id, json.loads(session_path.read_text()))
            self.assertIn(device.device_id, json.loads(device_path.read_text()))


if __name__ == "__main__":
    unittest.main()

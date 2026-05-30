import tempfile
import json
import os
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib import request as urllib_request

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.csrf import CSRF_HEADER
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import (
    ReplayGuard,
    decrypt_at_broker,
    encrypt_for_broker,
    generate_keypair,
    load_or_create_keypair,
)
from omnidoer.omni_control.server import ControlHandler
from tests.test_control_auth import public_jwk, sign_request


class CloudSecretSubmissionTest(unittest.TestCase):
    def test_cloud_secret_envelope_binds_device_and_expiry(self) -> None:
        keypair = generate_keypair()
        expires_at = 1780100000.0
        envelope = encrypt_for_broker(
            keypair.public_key_b64,
            {"password": "cloud-secret"},
            request_id="req_cloud",
            origin="https://agent.example.com",
            request_type="credential",
            device_id="dev_123",
            expires_at=expires_at,
        )
        self.assertEqual(envelope["device_id"], "dev_123")
        self.assertNotIn("cloud-secret", repr(envelope))
        payload = decrypt_at_broker(
            keypair.private_key_b64,
            envelope,
            request_id="req_cloud",
            origin="https://agent.example.com",
            request_type="credential",
        )
        self.assertEqual(payload["password"], "cloud-secret")
        with self.assertRaises(ValueError):
            decrypt_at_broker(
                keypair.private_key_b64,
                envelope,
                request_id="req_cloud",
                origin="https://agent.example.com",
                request_type="credential",
                device_id="dev_other",
                expires_at=expires_at,
            )

    def test_cloud_secret_replay_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keypair = generate_keypair()
            envelope = encrypt_for_broker(
                keypair.public_key_b64,
                {"code": "654321"},
                request_id="req_cloud",
                origin="https://agent.example.com",
                request_type="sms_code",
                device_id="dev_123",
                expires_at=1780100000.0,
            )
            guard = ReplayGuard(Path(tmp) / "replay.json")
            decrypt_at_broker(
                keypair.private_key_b64,
                envelope,
                request_id="req_cloud",
                origin="https://agent.example.com",
                request_type="sms_code",
                device_id="dev_123",
                expires_at=1780100000.0,
                replay_guard=guard,
            )
            with self.assertRaises(ValueError):
                decrypt_at_broker(
                    keypair.private_key_b64,
                    envelope,
                    request_id="req_cloud",
                    origin="https://agent.example.com",
                    request_type="sms_code",
                    device_id="dev_123",
                    expires_at=1780100000.0,
                    replay_guard=guard,
                )

    def test_cloud_http_submit_requires_signed_device_bound_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(
                host="127.0.0.1",
                port=8787,
                cloud_direct=True,
                public_url="https://agent.example.com",
                behind_reverse_proxy=True,
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                csrf = body["csrf_token"]
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="cloud credential",
                    allowed_device_id=device_id,
                )
                keypair = load_or_create_keypair()

                def submit(envelope: dict, nonce: str):
                    path = f"/api/requests/{control_request.request_id}/submit"
                    signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="POST", path=path, nonce=nonce)
                    return urllib_request.Request(
                        f"{base}{path}",
                        data=json.dumps({"envelope": envelope}).encode(),
                        headers={
                            "content-type": "application/json",
                            "origin": config.public_origin,
                            "cookie": cookie,
                            CSRF_HEADER: csrf,
                            DEVICE_ID_HEADER: device_id,
                            DEVICE_TS_HEADER: signed["timestamp"],
                            DEVICE_NONCE_HEADER: signed["nonce"],
                            DEVICE_SIG_HEADER: signed["signature"],
                        },
                        method="POST",
                    )

                wrong_device = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"password": "cloud-secret"},
                    request_id=control_request.request_id,
                    origin=control_request.origin,
                    request_type=control_request.request_type,
                    device_id="dev_other",
                    expires_at=control_request.expires_at,
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(submit(wrong_device, "nonce-submit-wrong-device"), timeout=5)

                wrong_expiry = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"password": "cloud-secret"},
                    request_id=control_request.request_id,
                    origin=control_request.origin,
                    request_type=control_request.request_type,
                    device_id=device_id,
                    expires_at=control_request.expires_at + 60,
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(submit(wrong_expiry, "nonce-submit-wrong-expiry"), timeout=5)

                correct = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"password": "cloud-secret"},
                    request_id=control_request.request_id,
                    origin=control_request.origin,
                    request_type=control_request.request_type,
                    device_id=device_id,
                    expires_at=control_request.expires_at,
                )
                with urllib_request.urlopen(submit(correct, "nonce-submit-correct"), timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(payload["status"], "fulfilled")
                self.assertNotIn("cloud-secret", repr(payload))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

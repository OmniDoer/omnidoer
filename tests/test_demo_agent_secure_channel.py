import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_agent.demo_agent import _wait_for_challenge_payload, _wait_for_request_payload
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import encrypt_for_broker, load_or_create_keypair


class DemoAgentSecureChannelTest(unittest.TestCase):
    def test_demo_agent_rejects_wrong_device_bound_secret_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                keypair = load_or_create_keypair()
                store = RequestStore(Path(tmp) / "control_requests.json")
                request = store.create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="demo agent credential",
                    allowed_device_id="dev_expected",
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"username": "demo", "password": "demo-agent-secret"},
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                    device_id="dev_other",
                    expires_at=request.expires_at,
                )
                store.submit_ciphertext(request.request_id, envelope)
                with self.assertRaises(ValueError):
                    _wait_for_request_payload(request.request_id, timeout_seconds=1)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_demo_agent_waits_for_encrypted_challenge_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                keypair = load_or_create_keypair()
                store = RequestStore(Path(tmp) / "control_requests.json")
                request = store.create(
                    "totp",
                    origin="https://example.com",
                    top_level_url="https://example.com/totp",
                    action_summary="demo totp",
                    challenge_type="totp",
                    requested_fields=["otp"],
                )
                envelope = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"code": "123456"},
                    request_id=request.request_id,
                    origin=request.origin,
                    request_type=request.request_type,
                )
                store.submit_ciphertext(request.request_id, envelope)

                payload = _wait_for_challenge_payload(request.request_id, timeout_seconds=1)
                self.assertEqual(payload["code"], "123456")
                self.assertEqual(store.get(request.request_id).status, "challenge_completed")
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertIn("challenge_response_received", raw_audit)
                self.assertNotIn("123456", raw_audit)
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

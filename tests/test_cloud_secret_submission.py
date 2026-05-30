import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.secure_channel import (
    ReplayGuard,
    decrypt_at_broker,
    encrypt_for_broker,
    generate_keypair,
)


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


if __name__ == "__main__":
    unittest.main()

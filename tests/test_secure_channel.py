import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_control.secure_channel import (
    ReplayGuard,
    decrypt_at_broker,
    decrypt_web_at_broker,
    encrypt_for_broker,
    encrypt_for_broker_web,
    generate_keypair,
    generate_web_keypair,
)


class SecureChannelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keypair = generate_keypair()

    def test_encrypt_decrypt_round_trip(self) -> None:
        envelope = encrypt_for_broker(
            self.keypair.public_key_b64,
            {"username": "demo", "password": "fake-secret"},
            request_id="req_1",
            origin="http://127.0.0.1:8765",
            request_type="credential",
        )
        payload = decrypt_at_broker(
            self.keypair.private_key_b64,
            envelope,
            request_id="req_1",
            origin="http://127.0.0.1:8765",
            request_type="credential",
        )
        self.assertEqual(payload, {"username": "demo", "password": "fake-secret"})
        self.assertNotIn("fake-secret", repr(envelope))

    def test_wrong_associated_data_rejected(self) -> None:
        envelope = encrypt_for_broker(
            self.keypair.public_key_b64,
            {"code": "123456"},
            request_id="req_1",
            origin="http://127.0.0.1:8765",
            request_type="sms_code",
        )
        with self.assertRaises(ValueError):
            decrypt_at_broker(
                self.keypair.private_key_b64,
                envelope,
                request_id="req_2",
                origin="http://127.0.0.1:8765",
                request_type="sms_code",
            )

    def test_replay_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = ReplayGuard(Path(tmp) / "replay.json")
            envelope = encrypt_for_broker(
                self.keypair.public_key_b64,
                {"code": "123456"},
                request_id="req_1",
                origin="http://127.0.0.1:8765",
                request_type="sms_code",
            )
            decrypt_at_broker(
                self.keypair.private_key_b64,
                envelope,
                request_id="req_1",
                origin="http://127.0.0.1:8765",
                request_type="sms_code",
                replay_guard=guard,
            )
            with self.assertRaises(ValueError):
                decrypt_at_broker(
                    self.keypair.private_key_b64,
                    envelope,
                    request_id="req_1",
                    origin="http://127.0.0.1:8765",
                    request_type="sms_code",
                    replay_guard=guard,
                )

    def test_web_crypto_compatible_envelope_round_trip(self) -> None:
        keypair = generate_web_keypair()
        envelope = encrypt_for_broker_web(
            keypair.public_jwk,
            {"username": "demo", "password": "web-secret"},
            request_id="req_web",
            origin="http://127.0.0.1:8765",
            request_type="credential",
        )
        payload = decrypt_web_at_broker(
            keypair.private_key_pem,
            envelope,
            request_id="req_web",
            origin="http://127.0.0.1:8765",
            request_type="credential",
        )
        self.assertEqual(payload["username"], "demo")
        self.assertEqual(payload["password"], "web-secret")
        self.assertNotIn("web-secret", repr(envelope))


if __name__ == "__main__":
    unittest.main()

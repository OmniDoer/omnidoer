import tempfile
import time
import unittest
from pathlib import Path

from omnidoer.omni_control.requests import RequestStore


class ControlRequestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = RequestStore(Path(self.tmp.name) / "requests.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_and_public_dict_excludes_ciphertext(self) -> None:
        req = self.store.create(
            "credential",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/login",
            action_summary="login",
            requested_fields=["username", "password"],
            allowed_device_id="dev_phone",
        )
        self.assertEqual(req.status, "pending")
        public = req.to_public_dict()
        self.assertNotIn("response_ciphertext", public)
        self.assertEqual(public["allowed_device_id"], "dev_phone")
        self.assertFalse(public["secret_exposed_to_model"])

    def test_public_structured_details_are_redacted(self) -> None:
        req = self.store.create(
            "payment_approval",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/checkout",
            action_summary="pay",
            structured_details={"merchant": "Demo", "card": "4111 1111 1111 1111"},
        )
        public = req.to_public_dict()
        self.assertEqual(public["structured_details"]["merchant"], "Demo")
        self.assertNotIn("4111", repr(public))

    def test_ttl_expiry(self) -> None:
        req = self.store.create(
            "sms_code",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/sms",
            action_summary="sms",
            ttl_seconds=-1,
        )
        self.assertEqual(self.store.get(req.request_id).status, "expired")

    def test_submit_is_single_use(self) -> None:
        req = self.store.create(
            "credential",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/login",
            action_summary="login",
        )
        self.store.submit_ciphertext(req.request_id, {"ciphertext": "opaque"})
        with self.assertRaises(ValueError):
            self.store.submit_ciphertext(req.request_id, {"ciphertext": "opaque"})

    def test_takeover_state_flow(self) -> None:
        req = self.store.create(
            "human_takeover",
            origin="http://127.0.0.1:8765",
            top_level_url="http://127.0.0.1:8765/antibot",
            action_summary="take over",
            takeover_reason="high intensity anti-bot",
        )
        self.assertEqual(req.status, "user_control")
        self.assertEqual(req.control_owner, "user")
        released = self.store.release_takeover(req.request_id)
        self.assertEqual(released.status, "released")
        self.assertEqual(released.control_owner, "agent")
        self.assertTrue(released.completed_by_user)
        self.assertFalse(released.bypassed)


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest

from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_telegram.bridge import notification_for_request, reject_sensitive_input, status


class TelegramTest(unittest.TestCase):
    def test_telegram_disabled_for_sensitive_channels(self) -> None:
        text = status()
        self.assertIn("disabled", text)
        self.assertIn("notify-only", text)
        self.assertIn("Control Client", text)

    def test_notification_payload_contains_only_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            try:
                request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                )
                payload = notification_for_request(request, public_url="https://agent.example.com")
                self.assertFalse(payload["contains_secret"])
                self.assertFalse(payload["contains_challenge_answer"])
                self.assertFalse(payload["contains_takeover_stream"])
                self.assertEqual(payload["reason"], "sensitive_request_requires_control_client")
                self.assertIn("Control Client", payload["message"])
                self.assertNotIn("password", repr(payload))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_sensitive_input_is_rejected(self) -> None:
        with self.assertRaises(PermissionError):
            reject_sensitive_input("sms_code")


if __name__ == "__main__":
    unittest.main()

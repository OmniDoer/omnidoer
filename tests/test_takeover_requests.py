import os
import tempfile
import unittest
from pathlib import Path

from omnidoer.omni_takeover.relay import complete_in_test_mode, request_user_control, start_stream


class TakeoverRequestTest(unittest.TestCase):
    def test_takeover_user_control_release_and_no_input_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = {key: os.environ.get(key) for key in ("OMNIDOER_HOME", "OMNIDOER_TAKEOVER_TEST_MODE", "OMNIDOER_TEST_TAKEOVER_ACTIONS")}
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_TAKEOVER_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_TAKEOVER_ACTIONS"] = "tap:100,100;type:sensitive-user-input;release"
            try:
                req = request_user_control(
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/antibot",
                    reason="high intensity anti-bot",
                )
                frame = start_stream(req.request_id)
                self.assertTrue(frame["for_control_client_only"])
                result = complete_in_test_mode(req.request_id)
                self.assertEqual(result["status"], "user_completed_takeover")
                self.assertFalse(result["bypassed"])
                raw_audit = (Path(tmp) / "audit.jsonl").read_text()
                self.assertNotIn("sensitive-user-input", raw_audit)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()

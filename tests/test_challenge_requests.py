import os
import tempfile
import unittest

from omnidoer.omni_challenge.relay import complete_in_test_mode, request_user_interaction


class ChallengeRequestTest(unittest.TestCase):
    def test_challenge_status_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            old_mode = os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE")
            old_code = os.environ.get("OMNIDOER_TEST_SMS_CODE")
            os.environ["OMNIDOER_HOME"] = tmp
            os.environ["OMNIDOER_CHALLENGE_TEST_MODE"] = "1"
            os.environ["OMNIDOER_TEST_SMS_CODE"] = "123456"
            try:
                req = request_user_interaction(
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/sms",
                    challenge_type="sms",
                    reason="sms verification",
                    fields=["code"],
                )
                result = complete_in_test_mode(req.request_id)
                self.assertEqual(result["status"], "challenge_completed")
                self.assertTrue(result["completed_by_user"])
                self.assertFalse(result["bypassed"])
                self.assertNotIn("123456", repr(result))
            finally:
                for key, old in {
                    "OMNIDOER_HOME": old_home,
                    "OMNIDOER_CHALLENGE_TEST_MODE": old_mode,
                    "OMNIDOER_TEST_SMS_CODE": old_code,
                }.items():
                    if old is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = old


if __name__ == "__main__":
    unittest.main()

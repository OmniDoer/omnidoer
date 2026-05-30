import unittest

from omnidoer.omni_challenge.detector import detect_challenge_from_url


class ChallengeRelayTest(unittest.TestCase):
    def test_demo_url_detection(self) -> None:
        self.assertEqual(detect_challenge_from_url("http://127.0.0.1:8765/captcha"), "captcha")
        self.assertEqual(detect_challenge_from_url("http://127.0.0.1:8765/checkout/3ds"), "3ds")
        self.assertIsNone(detect_challenge_from_url("http://127.0.0.1:8765/dashboard"))


if __name__ == "__main__":
    unittest.main()

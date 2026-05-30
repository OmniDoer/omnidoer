import unittest

from omnidoer.omni_control.security_headers import SECURITY_HEADERS
from omnidoer.omni_control.websocket import websocket_origin_allowed


class ControlCsrfOriginTest(unittest.TestCase):
    def test_websocket_origin_must_match_public_origin(self) -> None:
        self.assertTrue(websocket_origin_allowed("https://agent.example.com", "https://agent.example.com"))
        self.assertFalse(websocket_origin_allowed("https://evil.example", "https://agent.example.com"))
        self.assertFalse(websocket_origin_allowed(None, "https://agent.example.com"))

    def test_security_headers_present(self) -> None:
        self.assertIn("content-security-policy", SECURITY_HEADERS)
        self.assertIn("frame-ancestors 'none'", SECURITY_HEADERS["content-security-policy"])
        self.assertEqual(SECURITY_HEADERS["x-frame-options"], "DENY")
        self.assertEqual(SECURITY_HEADERS["cache-control"], "no-store")


if __name__ == "__main__":
    unittest.main()

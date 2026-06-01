import unittest

from omnidoer.omni_control.security_headers import SECURITY_HEADERS
from omnidoer.omni_control.websocket import (
    decode_device_auth_subprotocol,
    encode_device_auth_subprotocol,
    websocket_accept_key,
    websocket_origin_allowed,
    websocket_text_frame,
)


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

    def test_websocket_accept_key_and_text_frame(self) -> None:
        self.assertEqual(websocket_accept_key("dGhlIHNhbXBsZSBub25jZQ=="), "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")
        frame = websocket_text_frame({"event": "requests", "data": {"requests": []}})
        self.assertEqual(frame[0], 0x81)
        self.assertIn(b'"requests":[]', frame)

    def test_device_auth_subprotocol_roundtrip(self) -> None:
        protocol = encode_device_auth_subprotocol(
            device_id="dev_1",
            timestamp="1780100000",
            nonce="nonce",
            signature="sig",
        )
        parsed = decode_device_auth_subprotocol(f"chat, {protocol}")
        self.assertEqual(
            parsed,
            {
                "device_id": "dev_1",
                "timestamp": "1780100000",
                "nonce": "nonce",
                "signature": "sig",
                "subprotocol": protocol,
            },
        )
        protocol = encode_device_auth_subprotocol(
            device_id="dev_1",
            session_id="sess_1",
            timestamp="1780100001",
            nonce="nonce-2",
            signature="sig-2",
        )
        parsed = decode_device_auth_subprotocol(protocol)
        self.assertEqual(parsed["session_id"], "sess_1")


if __name__ == "__main__":
    unittest.main()

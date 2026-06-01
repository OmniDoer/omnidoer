import ssl
import unittest

from omnidoer.omni_control.server import CLIENT_DISCONNECT_EXCEPTIONS, ControlHandler


class _DisconnectingWriter:
    def write(self, data):
        raise ssl.SSLEOFError("client closed")


class ControlDisconnectTest(unittest.TestCase):
    def test_json_response_treats_ssl_eof_as_client_disconnect(self) -> None:
        handler = object.__new__(ControlHandler)
        handler.wfile = _DisconnectingWriter()
        handler.close_connection = False
        handler.send_response = lambda status: None
        handler.send_header = lambda name, value: None
        handler.end_headers = lambda: None

        handler._send_json(200, {"ok": True})

        self.assertTrue(handler.close_connection)

    def test_ssl_eof_is_classified_as_client_disconnect(self) -> None:
        self.assertIn(ssl.SSLEOFError, CLIENT_DISCONNECT_EXCEPTIONS)


if __name__ == "__main__":
    unittest.main()

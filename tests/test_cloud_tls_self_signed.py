import json
import http.client
import socket
import ssl
import unittest
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.server import ControlHandler, TLSAwareThreadingHTTPServer, _self_signed_context


class CloudTlsSelfSignedTest(unittest.TestCase):
    def test_self_signed_dev_context_serves_https_status(self) -> None:
        config = build_config(
            host="127.0.0.1",
            port=8787,
            cloud_direct=True,
            public_url="https://localhost:8787",
            tls_self_signed_dev=True,
        )
        server = TLSAwareThreadingHTTPServer(("127.0.0.1", 0), ControlHandler, tls_context=_self_signed_context("127.0.0.1"))
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_direct_tls = True  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            context = ssl._create_unverified_context()
            with urllib_request.urlopen(f"https://127.0.0.1:{server.server_address[1]}/api/status", context=context, timeout=5) as response:
                payload = json.loads(response.read().decode())
            self.assertEqual(payload["mode"], "cloud_direct")
            self.assertFalse(payload["agent_llm_receives_secrets"])
        finally:
            server.shutdown()
            server.server_close()

    def test_direct_tls_port_redirects_plain_http_without_query(self) -> None:
        config = build_config(
            host="127.0.0.1",
            port=8787,
            cloud_direct=True,
            public_url="https://localhost:8787",
            tls_self_signed_dev=True,
        )
        server = TLSAwareThreadingHTTPServer(("127.0.0.1", 0), ControlHandler, tls_context=_self_signed_context("127.0.0.1"))
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_direct_tls = True  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = None
        try:
            conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            conn.request("GET", "/")
            response = conn.getresponse()
            self.assertEqual(response.status, 308)
            self.assertEqual(response.getheader("location"), "https://localhost:8787/")
            self.assertIn("Use HTTPS", response.read().decode())
        finally:
            if conn:
                conn.close()
            server.shutdown()
            server.server_close()

    def test_direct_tls_port_does_not_redirect_pairing_query_from_plain_http(self) -> None:
        config = build_config(
            host="127.0.0.1",
            port=8787,
            cloud_direct=True,
            public_url="https://localhost:8787",
            tls_self_signed_dev=True,
        )
        server = TLSAwareThreadingHTTPServer(("127.0.0.1", 0), ControlHandler, tls_context=_self_signed_context("127.0.0.1"))
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_direct_tls = True  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        conn = None
        try:
            conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            conn.request("GET", "/pair?code=do-not-forward&pairing_id=pair_secret")
            response = conn.getresponse()
            body = response.read().decode()
            self.assertEqual(response.status, 400)
            self.assertIsNone(response.getheader("location"))
            self.assertIn("HTTPS", body)
            self.assertNotIn("do-not-forward", body)
        finally:
            if conn:
                conn.close()
            server.shutdown()
            server.server_close()

    def test_idle_tls_probe_does_not_block_pairing_page(self) -> None:
        config = build_config(
            host="127.0.0.1",
            port=8787,
            cloud_direct=True,
            public_url="https://localhost:8787",
            tls_self_signed_dev=True,
        )
        server = TLSAwareThreadingHTTPServer(("127.0.0.1", 0), ControlHandler, tls_context=_self_signed_context("127.0.0.1"))
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.omnidoer_direct_tls = True  # type: ignore[attr-defined]
        server.omnidoer_tls_accept_peek_timeout_seconds = 0.1  # type: ignore[attr-defined]
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        idle = None
        try:
            idle = socket.create_connection(("127.0.0.1", server.server_address[1]), timeout=5)
            context = ssl._create_unverified_context()
            with urllib_request.urlopen(f"https://127.0.0.1:{server.server_address[1]}/pair", context=context, timeout=5) as response:
                body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertIn("OmniDoer", body)
        finally:
            if idle:
                idle.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

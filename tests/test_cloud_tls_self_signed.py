import json
import ssl
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.server import ControlHandler, _self_signed_context


class CloudTlsSelfSignedTest(unittest.TestCase):
    def test_self_signed_dev_context_serves_https_status(self) -> None:
        config = build_config(
            host="127.0.0.1",
            port=8787,
            cloud_direct=True,
            public_url="https://localhost:8787",
            tls_self_signed_dev=True,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
        server.omnidoer_config = config  # type: ignore[attr-defined]
        server.socket = _self_signed_context("127.0.0.1").wrap_socket(server.socket, server_side=True)
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


if __name__ == "__main__":
    unittest.main()

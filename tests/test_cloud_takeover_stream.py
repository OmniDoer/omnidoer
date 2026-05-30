import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import ControlHandler


class CloudTakeoverStreamTest(unittest.TestCase):
    def test_cloud_takeover_frame_requires_authenticated_device(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(
                host="127.0.0.1",
                port=8787,
                cloud_direct=True,
                public_url="https://agent.example.com",
                behind_reverse_proxy=True,
            )
            request = RequestStore().create(
                "human_takeover",
                origin="https://example.com",
                top_level_url="https://example.com/antibot",
                action_summary="user takeover",
                browser_context_id="missing",
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with self.assertRaises(Exception):
                    urllib_request.urlopen(f"{base}/api/requests/{request.request_id}/frame", timeout=5)

                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                pair = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": "phone-key"}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with urllib_request.urlopen(pair, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                frame = urllib_request.Request(f"{base}/api/requests/{request.request_id}/frame", headers={"cookie": cookie})
                with urllib_request.urlopen(frame, timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertTrue(payload["for_control_client_only"])
                self.assertTrue(payload["not_for_llm"])
                self.assertIn("data_b64", payload)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

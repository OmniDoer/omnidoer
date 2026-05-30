import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import ControlHandler
from tests.test_control_auth import public_jwk, sign_request


PROXY_HEADERS = {"x-forwarded-proto": "https"}


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
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(pair, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                frame_path = f"/api/requests/{request.request_id}/frame"
                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path=frame_path)
                frame = urllib_request.Request(
                    f"{base}{frame_path}",
                    headers={
                        "cookie": cookie,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                )
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

    def test_cloud_takeover_frame_is_scoped_to_allowed_device(self) -> None:
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
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"

            def pair(name: str):
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": name, "device_public_key": public_jwk(key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    return key, response.headers["set-cookie"], json.loads(response.read().decode())

            def frame_request(key, cookie: str, body: dict, request_id: str, nonce: str):
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                frame_path = f"/api/requests/{request_id}/frame"
                signed = sign_request(key, device_id=device_id, session_id=session_id, method="GET", path=frame_path, nonce=nonce)
                return urllib_request.Request(
                    f"{base}{frame_path}",
                    headers={
                        "cookie": cookie,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                )

            try:
                key_a, cookie_a, body_a = pair("Phone A")
                key_b, cookie_b, body_b = pair("Phone B")
                takeover = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/antibot",
                    action_summary="scoped takeover",
                    browser_context_id="missing",
                    allowed_device_id=body_a["device"]["device_id"],
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(frame_request(key_b, cookie_b, body_b, takeover.request_id, "nonce-frame-b"), timeout=5)

                with urllib_request.urlopen(frame_request(key_a, cookie_a, body_a, takeover.request_id, "nonce-frame-a"), timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertTrue(payload["for_control_client_only"])
                self.assertTrue(payload["not_for_llm"])
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

import unittest
import json
import os
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.cloud import build_config, security_status
from omnidoer.omni_control.csrf import CSRF_HEADER
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.server import ControlHandler, sanitize_log_value
from tests.test_control_auth import public_jwk, sign_request


class CloudControlServiceTest(unittest.TestCase):
    def test_refuses_public_bind_without_cloud_direct(self) -> None:
        with self.assertRaises(ValueError):
            build_config(host="0.0.0.0", port=8787)

    def test_cloud_direct_requires_https_or_explicit_insecure_dev(self) -> None:
        with self.assertRaises(ValueError):
            build_config(host="0.0.0.0", port=8787, cloud_direct=True, public_url="http://agent.example.com")
        with self.assertRaises(ValueError):
            build_config(host="0.0.0.0", port=8787, cloud_direct=True, public_url="https://agent.example.com")

    def test_cloud_direct_behind_proxy(self) -> None:
        config = build_config(
            host="0.0.0.0",
            port=8787,
            cloud_direct=True,
            public_url="https://agent.example.com",
            behind_reverse_proxy=True,
        )
        status = security_status(config)
        self.assertEqual(config.mode, "cloud_direct")
        self.assertTrue(status["requires_pairing"])
        self.assertFalse(status["mcp_publicly_exposed"])
        self.assertFalse(status["vault_broker_publicly_exposed"])

    def test_local_dev_mode_allows_http_localhost(self) -> None:
        config = build_config(host="127.0.0.1", port=8787)
        self.assertEqual(config.mode, "local_dev")

    def test_control_service_logs_redact_pairing_query_and_tokens(self) -> None:
        self.assertEqual(
            sanitize_log_value("GET /pair?code=abc123&pairing_id=pair_secret HTTP/1.1"),
            "GET /pair?redacted HTTP/1.1",
        )
        self.assertEqual(
            sanitize_log_value("omnidoer_session=session:secret token=abc"),
            "omnidoer_session=[redacted] token=[redacted]",
        )

    def test_access_log_does_not_print_pairing_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            output = StringIO()
            try:
                with redirect_stdout(output):
                    try:
                        urllib_request.urlopen(f"{base}/pair?code=do-not-log-me&pairing_id=pair_secret", timeout=5)
                    except Exception:
                        pass
                text = output.getvalue()
                self.assertNotIn("do-not-log-me", text)
                self.assertNotIn("pair_secret", text)
                self.assertIn("/pair?redacted", text)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_direct_http_api_requires_pairing_session_and_csrf(self) -> None:
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
            try:
                with self.assertRaises(Exception):
                    urllib_request.urlopen(f"{base}/api/requests", timeout=5)

                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    self.assertEqual(response.status, 201)
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                self.assertIn("HttpOnly", cookie)
                self.assertNotIn("session_token", repr(body))
                csrf = body["csrf_token"]
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                with self.assertRaises(Exception):
                    urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers={"cookie": cookie}), timeout=5)

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path="/api/requests")
                signed_headers = {
                    "cookie": cookie,
                    DEVICE_ID_HEADER: device_id,
                    DEVICE_TS_HEADER: signed["timestamp"],
                    DEVICE_NONCE_HEADER: signed["nonce"],
                    DEVICE_SIG_HEADER: signed["signature"],
                }
                authed = urllib_request.Request(f"{base}/api/requests", headers=signed_headers)
                with urllib_request.urlopen(authed, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                with self.assertRaises(Exception):
                    urllib_request.urlopen(authed, timeout=5)

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="POST", path="/api/tasks", nonce="nonce-no-csrf")
                no_csrf = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "run"}).encode(),
                    headers={
                        "content-type": "application/json",
                        "cookie": cookie,
                        "origin": config.public_origin,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                    method="POST",
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(no_csrf, timeout=5)

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="POST", path="/api/tasks", nonce="nonce-with-csrf")
                with_csrf = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "run"}).encode(),
                    headers={
                        "content-type": "application/json",
                        "cookie": cookie,
                        "origin": config.public_origin,
                        CSRF_HEADER: csrf,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                    method="POST",
                )
                with urllib_request.urlopen(with_csrf, timeout=5) as response:
                    self.assertEqual(response.status, 201)

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path="/api/events", nonce="nonce-events")
                events = urllib_request.Request(
                    f"{base}/api/events",
                    headers={
                        "cookie": cookie,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                )
                with urllib_request.urlopen(events, timeout=5) as response:
                    self.assertEqual(response.headers["content-type"].split(";")[0], "text/event-stream")
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

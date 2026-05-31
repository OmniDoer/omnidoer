import unittest
import base64
import json
import os
import socket
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
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import ControlHandler, sanitize_log_value
from omnidoer.omni_control.secure_channel import encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_control.websocket import encode_device_auth_subprotocol
from tests.test_control_auth import public_jwk, sign_request


PROXY_HEADERS = {"x-forwarded-proto": "https"}


def read_websocket_text(sock: socket.socket, initial: bytes = b"") -> str:
    data = initial
    while len(data) < 2:
        data += sock.recv(4096)
    length = data[1] & 0x7F
    offset = 2
    if length == 126:
        while len(data) < offset + 2:
            data += sock.recv(4096)
        length = int.from_bytes(data[offset : offset + 2], "big")
        offset += 2
    elif length == 127:
        while len(data) < offset + 8:
            data += sock.recv(4096)
        length = int.from_bytes(data[offset : offset + 8], "big")
        offset += 8
    while len(data) < offset + length:
        data += sock.recv(4096)
    return data[offset : offset + length].decode()


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

    def test_pair_route_serves_pwa_index(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urllib_request.urlopen(f"{base}/pair?code=demo&pairing_id=pair_demo", timeout=5) as response:
                body = response.read().decode()
            self.assertIn("OmniDoer Control Client", body)
            self.assertIn("/app.js", body)
            self.assertNotIn("pair_demo", body)
        finally:
            server.shutdown()
            server.server_close()

    def test_local_bind_with_public_url_requires_cloud_direct(self) -> None:
        with self.assertRaises(ValueError):
            build_config(host="127.0.0.1", port=8787, public_url="https://agent.example.com")

    def test_lan_mode_requires_pairing_session_and_csrf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="192.168.1.20", port=8787, public_url="http://192.168.1.20:8787")
            self.assertEqual(config.mode, "lan")
            self.assertTrue(security_status(config)["requires_authentication"])
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with self.assertRaises(Exception):
                    urllib_request.urlopen(f"{base}/api/requests", timeout=5)
                with self.assertRaises(Exception):
                    urllib_request.urlopen(f"{base}/api/broker-key", timeout=5)

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
                csrf = body["csrf_token"]
                self.assertIn("HttpOnly", cookie)
                self.assertNotIn("session_token", repr(body))

                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers={"cookie": cookie}), timeout=5) as response:
                    self.assertEqual(response.status, 200)
                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/broker-key", headers={"cookie": cookie}), timeout=5) as response:
                    self.assertEqual(response.status, 200)

                wrong_origin = urllib_request.Request(f"{base}/api/requests", headers={"cookie": cookie, "origin": "http://evil.example"})
                with self.assertRaises(Exception):
                    urllib_request.urlopen(wrong_origin, timeout=5)

                no_csrf = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "run"}).encode(),
                    headers={"content-type": "application/json", "cookie": cookie, "origin": config.public_origin},
                    method="POST",
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(no_csrf, timeout=5)

                with_csrf = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "run"}).encode(),
                    headers={"content-type": "application/json", "cookie": cookie, "origin": config.public_origin, CSRF_HEADER: csrf},
                    method="POST",
                )
                with urllib_request.urlopen(with_csrf, timeout=5) as response:
                    self.assertEqual(response.status, 201)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_lan_request_can_be_scoped_to_one_device(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="192.168.1.20", port=8787, public_url="http://192.168.1.20:8787")
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"

            def pair(name: str):
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                key = ec.generate_private_key(ec.SECP256R1())
                request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": name, "device_public_key": public_jwk(key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    return response.headers["set-cookie"], json.loads(response.read().decode())

            try:
                cookie_a, body_a = pair("Phone A")
                cookie_b, body_b = pair("Phone B")
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="LAN scoped login",
                    allowed_device_id=body_a["device"]["device_id"],
                )

                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers={"cookie": cookie_a}), timeout=5) as response:
                    visible_a = json.loads(response.read().decode())
                self.assertEqual([item["request_id"] for item in visible_a], [control_request.request_id])

                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers={"cookie": cookie_b}), timeout=5) as response:
                    visible_b = json.loads(response.read().decode())
                self.assertEqual(visible_b, [])

                with self.assertRaises(Exception):
                    urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests/{control_request.request_id}", headers={"cookie": cookie_b}), timeout=5)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_lan_secret_submit_requires_device_bound_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            config = build_config(host="192.168.1.20", port=8787, public_url="http://192.168.1.20:8787")
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            server.omnidoer_config = config  # type: ignore[attr-defined]
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                device_id = body["device"]["device_id"]
                csrf = body["csrf_token"]
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="LAN credential",
                    allowed_device_id=device_id,
                )
                keypair = load_or_create_keypair()

                def submit(envelope: dict):
                    path = f"/api/requests/{control_request.request_id}/submit"
                    return urllib_request.Request(
                        f"{base}{path}",
                        data=json.dumps({"envelope": envelope}).encode(),
                        headers={"content-type": "application/json", "origin": config.public_origin, "cookie": cookie, CSRF_HEADER: csrf},
                        method="POST",
                    )

                wrong_device = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"password": "lan-secret"},
                    request_id=control_request.request_id,
                    origin=control_request.origin,
                    request_type=control_request.request_type,
                    device_id="dev_other",
                    expires_at=control_request.expires_at,
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(submit(wrong_device), timeout=5)

                correct = encrypt_for_broker(
                    keypair.public_key_b64,
                    {"password": "lan-secret"},
                    request_id=control_request.request_id,
                    origin=control_request.origin,
                    request_type=control_request.request_type,
                    device_id=device_id,
                    expires_at=control_request.expires_at,
                )
                with urllib_request.urlopen(submit(correct), timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(payload["status"], "fulfilled")
                self.assertNotIn("lan-secret", repr(payload))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

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

    def test_pairing_metadata_endpoint_is_public_but_not_secret_bearing(self) -> None:
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
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                with urllib_request.urlopen(f"{base}/api/pairing/{pairing.pairing_id}", timeout=5) as response:
                    payload = json.loads(response.read().decode())
                self.assertEqual(response.status, 200)
                self.assertEqual(payload["public_url"], config.public_url)
                self.assertIn("broker_fingerprint", payload)
                self.assertIn("web_broker_fingerprint", payload)
                self.assertNotIn("code", payload)
                self.assertNotIn("code_hash", payload)
                self.assertNotIn(pairing.code, repr(payload))
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
                with self.assertRaises(Exception):
                    urllib_request.urlopen(f"{base}/api/broker-key", timeout=5)

                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                missing_proto_pair = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin},
                    method="POST",
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(missing_proto_pair, timeout=5)
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
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
                    **PROXY_HEADERS,
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

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path="/api/broker-key", nonce="nonce-broker-key")
                broker_key = urllib_request.Request(
                    f"{base}/api/broker-key",
                    headers={
                        "cookie": cookie,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                )
                with urllib_request.urlopen(broker_key, timeout=5) as response:
                    self.assertEqual(response.status, 200)

                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="POST", path="/api/tasks", nonce="nonce-no-csrf")
                no_csrf = urllib_request.Request(
                    f"{base}/api/tasks",
                    data=json.dumps({"text": "run"}).encode(),
                    headers={
                        "content-type": "application/json",
                        "cookie": cookie,
                        "origin": config.public_origin,
                        **PROXY_HEADERS,
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
                        **PROXY_HEADERS,
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
                        **PROXY_HEADERS,
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

    def test_cloud_direct_behind_proxy_accepts_forwarded_proto_header(self) -> None:
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
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, "forwarded": "for=127.0.0.1;proto=https;host=agent.example.com"},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    self.assertEqual(response.status, 201)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_direct_request_can_be_scoped_to_one_device(self) -> None:
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
                request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": name, "device_public_key": public_jwk(key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    return key, response.headers["set-cookie"], json.loads(response.read().decode())

            def signed_headers(key, body: dict, path: str, nonce: str) -> dict[str, str]:
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                signed = sign_request(key, device_id=device_id, session_id=session_id, method="GET", path=path, nonce=nonce)
                return {
                    "cookie": body["cookie"],
                    **PROXY_HEADERS,
                    DEVICE_ID_HEADER: device_id,
                    DEVICE_TS_HEADER: signed["timestamp"],
                    DEVICE_NONCE_HEADER: signed["nonce"],
                    DEVICE_SIG_HEADER: signed["signature"],
                }

            try:
                key_a, cookie_a, body_a = pair("Phone A")
                key_b, cookie_b, body_b = pair("Phone B")
                body_a["cookie"] = cookie_a
                body_b["cookie"] = cookie_b
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="scoped login",
                    allowed_device_id=body_a["device"]["device_id"],
                )

                headers_a = signed_headers(key_a, body_a, "/api/requests", "nonce-list-a")
                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers=headers_a), timeout=5) as response:
                    visible_a = json.loads(response.read().decode())
                self.assertEqual([item["request_id"] for item in visible_a], [control_request.request_id])

                headers_b = signed_headers(key_b, body_b, "/api/requests", "nonce-list-b")
                with urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers=headers_b), timeout=5) as response:
                    visible_b = json.loads(response.read().decode())
                self.assertEqual(visible_b, [])

                path = f"/api/requests/{control_request.request_id}"
                headers_b_detail = signed_headers(key_b, body_b, path, "nonce-detail-b")
                with self.assertRaises(Exception):
                    urllib_request.urlopen(urllib_request.Request(f"{base}{path}", headers=headers_b_detail), timeout=5)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_direct_stream_filters_requests_by_signed_device(self) -> None:
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
                request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": name, "device_public_key": public_jwk(key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    return key, response.headers["set-cookie"], json.loads(response.read().decode())

            def signed_stream_headers(key, body: dict, cookie: str, nonce: str) -> dict[str, str]:
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                signed = sign_request(key, device_id=device_id, session_id=session_id, method="GET", path="/api/events", nonce=nonce)
                return {
                    "cookie": cookie,
                    **PROXY_HEADERS,
                    DEVICE_ID_HEADER: device_id,
                    DEVICE_TS_HEADER: signed["timestamp"],
                    DEVICE_NONCE_HEADER: signed["nonce"],
                    DEVICE_SIG_HEADER: signed["signature"],
                }

            try:
                key_a, cookie_a, body_a = pair("Phone A")
                key_b, cookie_b, body_b = pair("Phone B")
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="streamed login",
                    allowed_device_id=body_a["device"]["device_id"],
                )

                stream_url = f"{base}/api/events?stream=1&snapshots=1&interval=0"
                headers_b = signed_stream_headers(key_b, body_b, cookie_b, "nonce-stream-b")
                with urllib_request.urlopen(urllib_request.Request(stream_url, headers=headers_b), timeout=5) as response:
                    self.assertEqual(response.headers["content-type"].split(";")[0], "text/event-stream")
                    hidden = response.read().decode()
                self.assertIn('"requests":[]', hidden)
                self.assertNotIn(control_request.request_id, hidden)

                headers_a = signed_stream_headers(key_a, body_a, cookie_a, "nonce-stream-a")
                with urllib_request.urlopen(urllib_request.Request(stream_url, headers=headers_a), timeout=5) as response:
                    visible = response.read().decode()
                self.assertIn("event: requests", visible)
                self.assertIn(control_request.request_id, visible)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_direct_websocket_push_uses_signed_device_protocol(self) -> None:
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
                pairing = PairingStore().create(public_url=config.public_url, ttl_seconds=600)
                device_key = ec.generate_private_key(ec.SECP256R1())
                pair_request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": "Phone", "device_public_key": public_jwk(device_key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(pair_request, timeout=5) as response:
                    cookie = response.headers["set-cookie"]
                    body = json.loads(response.read().decode())
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                control_request = RequestStore().create(
                    "credential",
                    origin="https://example.com",
                    top_level_url="https://example.com/login",
                    action_summary="websocket login",
                    allowed_device_id=device_id,
                )
                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path="/api/ws/requests", nonce="nonce-ws")
                protocol = encode_device_auth_subprotocol(
                    device_id=device_id,
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                )
                websocket_key = base64.b64encode(os.urandom(16)).decode()
                request_text = "\r\n".join(
                    [
                        "GET /api/ws/requests?snapshots=1&interval=0 HTTP/1.1",
                        "Host: agent.example.com",
                        "Upgrade: websocket",
                        "Connection: Upgrade",
                        f"Sec-WebSocket-Key: {websocket_key}",
                        "Sec-WebSocket-Version: 13",
                        f"Sec-WebSocket-Protocol: {protocol}",
                        f"Origin: {config.public_origin}",
                        "X-Forwarded-Proto: https",
                        f"Cookie: {cookie}",
                        "",
                        "",
                    ]
                ).encode()
                with socket.create_connection(("127.0.0.1", server.server_address[1]), timeout=5) as sock:
                    sock.sendall(request_text)
                    data = b""
                    while b"\r\n\r\n" not in data:
                        data += sock.recv(4096)
                    headers, frame = data.split(b"\r\n\r\n", 1)
                    self.assertIn(b"101 Switching Protocols", headers)
                    self.assertIn(protocol.encode(), headers)
                    payload = json.loads(read_websocket_text(sock, frame))
                self.assertEqual(payload["event"], "requests")
                self.assertIn(control_request.request_id, repr(payload["data"]))
                self.assertNotIn("password", repr(payload))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_direct_can_revoke_sessions_and_devices(self) -> None:
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
                request = urllib_request.Request(
                    f"{base}/api/pair",
                    data=json.dumps({"code": pairing.code, "device_name": name, "device_public_key": public_jwk(key)}).encode(),
                    headers={"content-type": "application/json", "origin": config.public_origin, **PROXY_HEADERS},
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    return key, response.headers["set-cookie"], json.loads(response.read().decode())

            def signed_headers(key, body: dict, cookie: str, method: str, path: str, nonce: str, *, csrf: bool = False) -> dict[str, str]:
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                signed = sign_request(key, device_id=device_id, session_id=session_id, method=method, path=path, nonce=nonce)
                headers = {
                    "cookie": cookie,
                    **PROXY_HEADERS,
                    DEVICE_ID_HEADER: device_id,
                    DEVICE_TS_HEADER: signed["timestamp"],
                    DEVICE_NONCE_HEADER: signed["nonce"],
                    DEVICE_SIG_HEADER: signed["signature"],
                }
                if csrf:
                    headers["origin"] = config.public_origin
                    headers[CSRF_HEADER] = body["csrf_token"]
                    headers["content-type"] = "application/json"
                return headers

            try:
                admin_key, admin_cookie, admin_body = pair("Admin")
                phone_key, phone_cookie, phone_body = pair("Phone")
                phone_session_id = phone_body["session"]["session_id"]
                phone_device_id = phone_body["device"]["device_id"]

                session_revoke_path = f"/api/sessions/{phone_session_id}/revoke"
                request = urllib_request.Request(
                    f"{base}{session_revoke_path}",
                    data=b"{}",
                    headers=signed_headers(admin_key, admin_body, admin_cookie, "POST", session_revoke_path, "nonce-revoke-session", csrf=True),
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    revoked = json.loads(response.read().decode())
                self.assertEqual(revoked["status"], "revoked")
                self.assertEqual(revoked["session"]["session_id"], phone_session_id)
                self.assertNotIn("token", repr(revoked))

                with self.assertRaises(Exception):
                    headers = signed_headers(phone_key, phone_body, phone_cookie, "GET", "/api/requests", "nonce-after-session-revoke")
                    urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers=headers), timeout=5)

                phone_key, phone_cookie, phone_body = pair("Phone Again")
                phone_device_id = phone_body["device"]["device_id"]
                device_revoke_path = f"/api/devices/{phone_device_id}/revoke"
                request = urllib_request.Request(
                    f"{base}{device_revoke_path}",
                    data=b"{}",
                    headers=signed_headers(admin_key, admin_body, admin_cookie, "POST", device_revoke_path, "nonce-revoke-device", csrf=True),
                    method="POST",
                )
                with urllib_request.urlopen(request, timeout=5) as response:
                    revoked = json.loads(response.read().decode())
                self.assertEqual(revoked["status"], "revoked")
                self.assertEqual(revoked["device"]["device_id"], phone_device_id)
                self.assertTrue(revoked["revoked_sessions"])
                self.assertNotIn("public_key", repr(revoked))

                with self.assertRaises(Exception):
                    headers = signed_headers(phone_key, phone_body, phone_cookie, "GET", "/api/requests", "nonce-after-device-revoke")
                    urllib_request.urlopen(urllib_request.Request(f"{base}/api/requests", headers=headers), timeout=5)

                raw_audit = os.path.join(tmp, "audit.jsonl")
                with open(raw_audit, encoding="utf-8") as handle:
                    audit_text = handle.read()
                self.assertIn("control_device_paired", audit_text)
                self.assertIn("control_session_revoked", audit_text)
                self.assertIn("control_device_revoked", audit_text)
                self.assertNotIn("session_token", audit_text)
                self.assertNotIn("public_key", audit_text)
                self.assertNotIn("nonce-revoke", audit_text)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

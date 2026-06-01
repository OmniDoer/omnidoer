import json
import os
import base64
import socket
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib import request as urllib_request
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import ec

from omnidoer.omni_control.cloud import build_config
from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.csrf import CSRF_HEADER
from omnidoer.omni_control.device_signing import DEVICE_ID_HEADER, DEVICE_NONCE_HEADER, DEVICE_SIG_HEADER, DEVICE_TS_HEADER
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.server import (
    BROWSER_CONTEXT_STREAM_DEFAULT_SNAPSHOTS,
    BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS,
    BROWSER_CONTEXT_STREAM_MAX_SNAPSHOTS,
    BROWSER_FRAME_STREAM_DEFAULT_SNAPSHOTS,
    BROWSER_FRAME_STREAM_MAX_SNAPSHOTS,
    ControlHandler,
)
from omnidoer.omni_control.websocket import encode_device_auth_subprotocol
from omnidoer.omni_takeover.cross_process import write_context_status, write_frame
from omnidoer.omni_takeover.sessions import registered_browser_context
from omnidoer.omni_takeover.stream import frame_from_image
from tests.test_control_auth import public_jwk, sign_request


PROXY_HEADERS = {"x-forwarded-proto": "https"}


class ProfileAwareBrowser:
    def __init__(self):
        self.frame_profile = None

    def takeover_frame(self, *, frame_profile: str | None = None) -> dict:
        self.frame_profile = frame_profile
        return frame_from_image(
            b"compressed-takeover-frame",
            url="https://example.com/antibot",
            origin="https://example.com",
            viewport_width=320,
            viewport_height=180,
            content_type="image/jpeg",
            frame_profile=frame_profile,
            quality=48,
        )


class ContextStatusBrowser:
    def current_url(self) -> str:
        return "https://example.com/working"

    def current_origin(self) -> str:
        return "https://example.com"


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


class CloudTakeoverStreamTest(unittest.TestCase):
    def test_browser_stream_defaults_keep_mobile_takeover_connected_longer(self) -> None:
        self.assertEqual(BROWSER_CONTEXT_STREAM_DEFAULT_SNAPSHOTS, 1200)
        self.assertEqual(BROWSER_CONTEXT_STREAM_MAX_SNAPSHOTS, 1200)
        self.assertEqual(BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS, 30.0)
        self.assertEqual(BROWSER_FRAME_STREAM_DEFAULT_SNAPSHOTS, 1200)
        self.assertEqual(BROWSER_FRAME_STREAM_MAX_SNAPSHOTS, 1200)

    def test_browser_context_stream_sends_heartbeat_when_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with patch("omnidoer.omni_control.server.BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS", 0.0):
                    with urllib_request.urlopen(
                        f"{base}/api/browser/contexts/events?stream=1&snapshots=2&interval=0",
                        timeout=5,
                    ) as response:
                        stream = response.read().decode()
                self.assertEqual(stream.count("event: browser_contexts"), 1)
                self.assertIn("event: heartbeat", stream)
                self.assertIn('"secret_exposed_to_model":false', stream)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_takeover_frame_endpoint_passes_adaptive_profile_to_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            server = ThreadingHTTPServer(("127.0.0.1", 0), ControlHandler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            browser = ProfileAwareBrowser()
            try:
                takeover = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/antibot",
                    action_summary="adaptive profile takeover",
                    browser_context_id="profile-browser",
                )
                with registered_browser_context("profile-browser", browser):
                    with urllib_request.urlopen(f"{base}/api/requests/{takeover.request_id}/frame?profile=data_saver", timeout=5) as response:
                        payload = json.loads(response.read().decode())
                self.assertEqual(browser.frame_profile, "data_saver")
                self.assertEqual(payload["content_type"], "image/jpeg")
                self.assertEqual(payload["transport"]["profile"], "data_saver")
                self.assertEqual(payload["transport"]["quality"], 48)
                RequestStore().validate_takeover_frame(takeover.request_id, payload["frame_id"])
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

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
            context_id = "cloud-frame-browser"
            request = RequestStore().create(
                "human_takeover",
                origin="https://example.com",
                top_level_url="https://example.com/antibot",
                action_summary="user takeover",
                browser_context_id=context_id,
            )
            write_frame(
                context_id,
                frame_from_image(
                    b"authenticated-takeover-frame",
                    url="https://example.com/antibot",
                    origin="https://example.com",
                    viewport_width=320,
                    viewport_height=180,
                    content_type="image/jpeg",
                    frame_profile="data_saver",
                    quality=48,
                ),
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

    def test_cloud_takeover_frame_websocket_uses_signed_device_protocol(self) -> None:
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
                context_id = "takeover-ws-browser"
                write_frame(
                    context_id,
                    frame_from_image(
                        b"websocket-takeover-frame",
                        url="https://example.com/antibot",
                        origin="https://example.com",
                        viewport_width=320,
                        viewport_height=180,
                        content_type="image/jpeg",
                        frame_profile="data_saver",
                        quality=48,
                    ),
                )
                takeover = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/antibot",
                    action_summary="websocket takeover",
                    browser_context_id=context_id,
                    allowed_device_id=device_id,
                )
                frame_path = f"/api/ws/requests/{takeover.request_id}/frames"
                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path=frame_path, nonce="nonce-frame-ws")
                protocol = encode_device_auth_subprotocol(
                    device_id=device_id,
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                )
                websocket_key = base64.b64encode(os.urandom(16)).decode()
                request_text = "\r\n".join(
                    [
                        f"GET {frame_path}?snapshots=1&interval=0 HTTP/1.1",
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
                self.assertEqual(payload["event"], "takeover_frame")
                self.assertEqual(payload["request_id"], takeover.request_id)
                self.assertTrue(payload["data"]["for_control_client_only"])
                self.assertTrue(payload["data"]["not_for_llm"])
                RequestStore().validate_takeover_frame(takeover.request_id, payload["data"]["frame_id"])
                self.assertNotIn("password", repr(payload))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_browser_context_preview_websocket_uses_signed_device_protocol(self) -> None:
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
                context_id = "preview-context"
                write_context_status(context_id, ContextStatusBrowser())
                write_frame(
                    context_id,
                    frame_from_image(
                        b"live-preview-frame",
                        url="https://example.com/working",
                        origin="https://example.com",
                        viewport_width=320,
                        viewport_height=180,
                        content_type="image/jpeg",
                        frame_profile="data_saver",
                        quality=48,
                    ),
                )
                frame_path = f"/api/ws/browser/contexts/{context_id}/frames"
                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path=frame_path, nonce="nonce-preview-ws")
                protocol = encode_device_auth_subprotocol(
                    device_id=device_id,
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                )
                websocket_key = base64.b64encode(os.urandom(16)).decode()
                request_text = "\r\n".join(
                    [
                        f"GET {frame_path}?snapshots=1&interval=0 HTTP/1.1",
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
                self.assertEqual(payload["event"], "browser_context_frame")
                self.assertEqual(payload["browser_context_id"], context_id)
                self.assertTrue(payload["data"]["for_control_client_only"])
                self.assertTrue(payload["data"]["not_for_llm"])
                self.assertIn("data_b64", payload["data"])
                self.assertNotIn("password", repr(payload))
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
                context_id = "scoped-browser"
                write_frame(
                    context_id,
                    frame_from_image(
                        b"scoped-takeover-frame",
                        url="https://example.com/antibot",
                        origin="https://example.com",
                        viewport_width=320,
                        viewport_height=180,
                        content_type="image/jpeg",
                        frame_profile="data_saver",
                        quality=48,
                    ),
                )
                takeover = RequestStore().create(
                    "human_takeover",
                    origin="https://example.com",
                    top_level_url="https://example.com/antibot",
                    action_summary="scoped takeover",
                    browser_context_id=context_id,
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

    def test_cloud_browser_context_websocket_streams_active_contexts(self) -> None:
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
                context_id = "stream-context"
                write_context_status(context_id, ContextStatusBrowser())
                context_path = "/api/ws/browser/contexts"
                signed = sign_request(device_key, device_id=device_id, session_id=session_id, method="GET", path=context_path, nonce="nonce-context-ws")
                protocol = encode_device_auth_subprotocol(
                    device_id=device_id,
                    timestamp=signed["timestamp"],
                    nonce=signed["nonce"],
                    signature=signed["signature"],
                )
                websocket_key = base64.b64encode(os.urandom(16)).decode()
                request_text = "\r\n".join(
                    [
                        f"GET {context_path}?snapshots=1&interval=0 HTTP/1.1",
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
                self.assertEqual(payload["event"], "browser_contexts")
                self.assertIn(context_id, repr(payload["data"]["contexts"]))
                self.assertFalse(payload["data"]["secret_exposed_to_model"])
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_context_takeover_is_assigned_to_requesting_device(self) -> None:
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

            def takeover_request(key, cookie: str, body: dict, nonce: str):
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                csrf = body["csrf_token"]
                takeover_path = "/api/browser/contexts/scoped-context/takeover"
                signed = sign_request(key, device_id=device_id, session_id=session_id, method="POST", path=takeover_path, nonce=nonce)
                return urllib_request.Request(
                    f"{base}{takeover_path}",
                    data=json.dumps({"reason": "phone requested takeover"}).encode(),
                    headers={
                        "content-type": "application/json",
                        "origin": config.public_origin,
                        "cookie": cookie,
                        CSRF_HEADER: csrf,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                    method="POST",
                )

            try:
                key_a, cookie_a, body_a = pair("Phone A")
                key_b, cookie_b, body_b = pair("Phone B")
                write_context_status("scoped-context", ContextStatusBrowser())

                with urllib_request.urlopen(takeover_request(key_a, cookie_a, body_a, "nonce-context-a"), timeout=5) as response:
                    takeover = json.loads(response.read().decode())
                self.assertEqual(takeover["status"], "user_control")
                self.assertEqual(takeover["allowed_device_id"], body_a["device"]["device_id"])
                self.assertFalse(takeover["reused"])
                self.assertEqual(takeover["agent_pause"]["message"]["role"], "user")
                self.assertEqual(takeover["agent_pause"]["message"]["client_message_id"][:14], "control_pause_")
                self.assertFalse(takeover["agent_pause"]["live_console_delivery"]["secret_exposed_to_model"])
                self.assertEqual(len(ChatStore().list()), 1)

                with self.assertRaises(Exception) as denied:
                    urllib_request.urlopen(takeover_request(key_b, cookie_b, body_b, "nonce-context-b"), timeout=5)
                self.assertIn("403", str(denied.exception))

                with urllib_request.urlopen(takeover_request(key_a, cookie_a, body_a, "nonce-context-a2"), timeout=5) as response:
                    reused = json.loads(response.read().decode())
                self.assertEqual(reused["request_id"], takeover["request_id"])
                self.assertTrue(reused["reused"])
                self.assertNotIn("agent_pause", reused)
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_cloud_registration_input_is_scoped_to_allowed_device(self) -> None:
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

            def input_request(key, cookie: str, body: dict, request_id: str, nonce: str):
                device_id = body["device"]["device_id"]
                session_id = body["session"]["session_id"]
                csrf = body["csrf_token"]
                input_path = f"/api/requests/{request_id}/input"
                signed = sign_request(key, device_id=device_id, session_id=session_id, method="POST", path=input_path, nonce=nonce)
                return urllib_request.Request(
                    f"{base}{input_path}",
                    data=json.dumps({"event_type": "type", "text": "not logged"}).encode(),
                    headers={
                        "content-type": "application/json",
                        "origin": config.public_origin,
                        "cookie": cookie,
                        CSRF_HEADER: csrf,
                        **PROXY_HEADERS,
                        DEVICE_ID_HEADER: device_id,
                        DEVICE_TS_HEADER: signed["timestamp"],
                        DEVICE_NONCE_HEADER: signed["nonce"],
                        DEVICE_SIG_HEADER: signed["signature"],
                    },
                    method="POST",
                )

            try:
                key_a, cookie_a, body_a = pair("Phone A")
                key_b, cookie_b, body_b = pair("Phone B")
                registration = RequestStore().create(
                    "account_registration",
                    origin="https://example.com",
                    top_level_url="https://example.com/register",
                    action_summary="registration handoff",
                    browser_context_id="missing",
                    allowed_device_id=body_a["device"]["device_id"],
                )
                with self.assertRaises(Exception):
                    urllib_request.urlopen(input_request(key_b, cookie_b, body_b, registration.request_id, "nonce-input-b"), timeout=5)

                with self.assertRaises(Exception) as allowed_but_no_browser:
                    urllib_request.urlopen(input_request(key_a, cookie_a, body_a, registration.request_id, "nonce-input-a"), timeout=5)
                self.assertIn("409", str(allowed_but_no_browser.exception))
            finally:
                server.shutdown()
                server.server_close()
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()

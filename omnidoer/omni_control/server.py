"""Local HTML5/PWA Control Client server."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import load_or_create_keypair


def static_root() -> Path:
    return Path(str(resources.files("omnidoer.omni_control") / "static"))


class ControlHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(static_root()), **kwargs)

    def log_message(self, fmt: str, *args: object) -> None:
        # Never log request bodies. Paths and response codes are enough for MVP diagnostics.
        print(f"{self.address_string()} - {fmt % args}")

    def _send_json(self, status: HTTPStatus, payload: dict | list) -> None:
        data = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        store = RequestStore()
        if path == "/api/status":
            self._send_json(HTTPStatus.OK, {"status": "ok", "mode": "local_trusted", "agent_llm_receives_secrets": False})
            return
        if path == "/api/broker-key":
            keypair = load_or_create_keypair()
            self._send_json(
                HTTPStatus.OK,
                {"public_key": keypair.public_key_b64, "fingerprint": keypair.fingerprint, "mode": "local_trusted"},
            )
            return
        if path == "/api/requests":
            self._send_json(HTTPStatus.OK, [request.to_public_dict() for request in store.list()])
            return
        if path.startswith("/api/requests/"):
            request_id = path.rsplit("/", 1)[-1]
            try:
                self._send_json(HTTPStatus.OK, store.get(request_id).to_public_dict())
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "request not found"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        store = RequestStore()
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "requests"]:
            request_id, action = parts[2], parts[3]
            try:
                if action == "approve":
                    request = store.approve(request_id)
                elif action == "deny":
                    request = store.deny(request_id)
                elif action == "release":
                    request = store.release_takeover(request_id)
                elif action == "complete-challenge":
                    request = store.mark_challenge_completed(request_id)
                elif action == "submit":
                    body = self._read_json()
                    request = store.submit_ciphertext(request_id, body.get("envelope", body))
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                    return
                self._send_json(HTTPStatus.OK, request.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("MVP local mode only allows 127.0.0.1/localhost")
    server = ThreadingHTTPServer((host, port), ControlHandler)
    print(f"OmniDoer Control Client listening on http://{host}:{port}/")
    server.serve_forever()

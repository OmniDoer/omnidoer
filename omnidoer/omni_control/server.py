"""Local HTML5/PWA Control Client server."""

from __future__ import annotations

import json
import re
import ssl
import tempfile
import ipaddress
import time
import datetime as dt
from http.cookies import SimpleCookie
from importlib import resources
from pathlib import Path
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from omnidoer.omni_control.auth import authenticate_session, authenticate_signed_session_request, pair_device
from omnidoer.omni_control.cloud import ControlServiceConfig, build_config
from omnidoer.omni_control.csrf import CSRF_HEADER, verify_csrf
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.device_signing import (
    DEVICE_ID_HEADER,
    DEVICE_NONCE_HEADER,
    DEVICE_SIG_HEADER,
    DEVICE_TS_HEADER,
)
from omnidoer.omni_control.rate_limit import RateLimiter
from omnidoer.omni_control.security_headers import apply_security_headers
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.secure_channel import load_or_create_keypair, load_or_create_web_keypair
from omnidoer.omni_control.sessions import ControlSession, SessionStore
from omnidoer.omni_control.tasks import TaskStore
from omnidoer.omni_takeover.input_events import event_from_dict
from omnidoer.omni_takeover.relay import apply_input_event, start_stream
from omnidoer.omni_takeover.sessions import get_browser_context


def static_root() -> Path:
    return Path(str(resources.files("omnidoer.omni_control") / "static"))


PAIR_RATE_LIMIT = RateLimiter(max_attempts=8, window_seconds=60, lockout_seconds=300)
CONTROL_MUTATION_RATE_LIMIT = RateLimiter(max_attempts=120, window_seconds=60, lockout_seconds=60)
SENSITIVE_LOG_PATTERNS = [
    re.compile(r"(omnidoer_session=)[^;\s]+"),
    re.compile(r"(code=)[^&\s]+"),
    re.compile(r"(pairing_id=)[^&\s]+"),
    re.compile(r"(token=)[^&\s]+"),
]


def sanitize_log_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value
    parts = text.split(" ", 2)
    if len(parts) == 3 and parts[0] in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        parsed = urlparse(parts[1])
        target = parsed.path
        if parsed.query:
            target = f"{target}?redacted"
        text = f"{parts[0]} {target} {parts[2]}"
    for pattern in SENSITIVE_LOG_PATTERNS:
        text = pattern.sub(r"\1[redacted]", text)
    return text


def _self_signed_context(host: str) -> ssl.SSLContext:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    names: list[x509.GeneralName] = [x509.DNSName("localhost")]
    try:
        names.append(x509.IPAddress(ipaddress.ip_address(host)))
    except ValueError:
        names.append(x509.DNSName(host))
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "OmniDoer Control Dev")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.datetime.utcnow() - dt.timedelta(minutes=1))
        .not_valid_after(dt.datetime.utcnow() + dt.timedelta(days=7))
        .add_extension(x509.SubjectAlternativeName(names), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_file = tempfile.NamedTemporaryFile("wb", delete=False, prefix="omnidoer-self-signed-", suffix=".crt")
    key_file = tempfile.NamedTemporaryFile("wb", delete=False, prefix="omnidoer-self-signed-", suffix=".key")
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    cert_file.close()
    key_file.close()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file.name, key_file.name)
    return context


class ControlHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(static_root()), **kwargs)

    def log_message(self, fmt: str, *args: object) -> None:
        # Never log request bodies. Paths and response codes are enough for MVP diagnostics.
        safe_args = tuple(sanitize_log_value(arg) for arg in args)
        print(f"{self.address_string()} - {fmt % safe_args}")

    def _send_json(self, status: HTTPStatus, payload: dict | list) -> None:
        data = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def end_headers(self) -> None:
        apply_security_headers(self.send_header)
        super().end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    @property
    def config(self) -> ControlServiceConfig:
        return getattr(self.server, "omnidoer_config", build_config(host="127.0.0.1", port=8787))

    def _sse_payload(self, store: RequestStore, session: ControlSession | None) -> dict:
        return {"requests": [request.to_public_dict() for request in self._visible_requests(store, session)]}

    def _send_sse(self, payload: dict) -> None:
        from omnidoer.omni_control.websocket import sse_event

        data = sse_event("requests", payload)
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_sse_stream(self, store: RequestStore, session: ControlSession | None, *, snapshots: int, interval: float) -> None:
        from omnidoer.omni_control.websocket import sse_event

        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("connection", "close")
        self.end_headers()
        for index in range(max(1, min(snapshots, 30))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            self.wfile.write(sse_event("requests", self._sse_payload(store, session)))
            self.wfile.flush()
        self.close_connection = True

    def _session_cookie(self) -> tuple[str | None, str | None]:
        cookie = SimpleCookie(self.headers.get("cookie", ""))
        morsel = cookie.get("omnidoer_session")
        if not morsel or ":" not in morsel.value:
            return None, None
        session_id, token = morsel.value.split(":", 1)
        return session_id, token

    def _origin_allowed(self) -> bool:
        if self.config.mode not in {"lan", "cloud_direct"}:
            return True
        origin = self.headers.get("origin")
        return not origin or origin == self.config.public_origin

    def _requires_pairing(self) -> bool:
        return self.config.mode in {"lan", "cloud_direct"}

    def _transport_allowed(self) -> bool:
        if self.config.mode != "cloud_direct" or not self.config.behind_reverse_proxy:
            return True
        forwarded_proto = (self.headers.get("x-forwarded-proto") or "").split(",", 1)[0].strip().lower()
        if forwarded_proto == "https":
            return True
        forwarded = self.headers.get("forwarded") or ""
        return bool(re.search(r"(?i)(^|[;,]\s*)proto=https($|[;,])", forwarded))

    def _authenticated_session(self):
        session_id, token = self._session_cookie()
        if not session_id or not token:
            raise PermissionError("session required")
        if self.config.mode == "cloud_direct":
            return authenticate_signed_session_request(
                session_id=session_id,
                session_token=token,
                device_id=self.headers.get(DEVICE_ID_HEADER, ""),
                method=self.command,
                path=urlparse(self.path).path,
                timestamp=self.headers.get(DEVICE_TS_HEADER, ""),
                nonce=self.headers.get(DEVICE_NONCE_HEADER, ""),
                signature=self.headers.get(DEVICE_SIG_HEADER, ""),
                device_store=DeviceStore(),
                session_store=SessionStore(),
            )
        return authenticate_session(session_id=session_id, session_token=token, device_store=DeviceStore(), session_store=SessionStore())

    def _require_access(self, *, mutating: bool = False):
        if not self._requires_pairing():
            return None
        if not self._transport_allowed():
            raise PermissionError("https proxy header required")
        if not self._origin_allowed():
            raise PermissionError("origin rejected")
        session = self._authenticated_session()
        if mutating and not verify_csrf(session.csrf_token, self.headers.get(CSRF_HEADER)):
            raise PermissionError("csrf rejected")
        return session

    def _request_allowed_for_session(self, request, session: ControlSession | None) -> bool:
        if not self._requires_pairing():
            return True
        return not request.allowed_device_id or (session is not None and request.allowed_device_id == session.device_id)

    def _visible_requests(self, store: RequestStore, session: ControlSession | None):
        return [request for request in store.list() if self._request_allowed_for_session(request, session)]

    def _get_request_for_session(self, store: RequestStore, request_id: str, session: ControlSession | None):
        request = store.get(request_id)
        if not self._request_allowed_for_session(request, session):
            raise PermissionError("request is not assigned to this device")
        return request

    def _validate_envelope_for_session(self, envelope: dict, request, session: ControlSession | None) -> None:
        if not self._requires_pairing():
            return
        if session is None:
            raise PermissionError("session required")
        if envelope.get("request_id") != request.request_id or envelope.get("origin") != request.origin or envelope.get("request_type") != request.request_type:
            raise PermissionError("envelope associated data mismatch")
        if envelope.get("device_id") != session.device_id:
            raise PermissionError("envelope device mismatch")
        if float(envelope.get("expires_at", "nan")) != float(request.expires_at):
            raise PermissionError("envelope expiry mismatch")

    def _set_session_cookie(self, session_id: str, token: str) -> None:
        secure = "; Secure" if self.config.mode == "cloud_direct" else ""
        self.send_header("set-cookie", f"omnidoer_session={session_id}:{token}; HttpOnly; SameSite=Strict{secure}; Path=/")

    def _remote_key(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _check_mutation_rate_limit(self, session: ControlSession | None) -> None:
        if not self._requires_pairing():
            return
        if session is None:
            raise PermissionError("session required")
        key = f"mutate:{session.device_id}:{urlparse(self.path).path}"
        CONTROL_MUTATION_RATE_LIMIT.check_and_record(key)

    def _send_permission_error(self, exc: PermissionError) -> None:
        if "rate limit" in str(exc):
            self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"})
            return
        self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        store = RequestStore()
        if path == "/api/status":
            config = getattr(self.server, "omnidoer_config", None)
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "mode": getattr(config, "mode", "local_dev"),
                    "public_url": getattr(config, "public_url", "http://127.0.0.1:8787"),
                    "agent_llm_receives_secrets": False,
                },
            )
            return
        if path.startswith("/api/pairing/"):
            pairing_id = path.rsplit("/", 1)[-1]
            try:
                pairing = PairingStore().get(pairing_id)
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "pairing not found"})
                return
            self._send_json(HTTPStatus.OK, pairing.to_public_dict())
            return
        if path == "/api/broker-key":
            try:
                self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            keypair = load_or_create_keypair()
            web_keypair = load_or_create_web_keypair()
            self._send_json(
                HTTPStatus.OK,
                {
                    "public_key": keypair.public_key_b64,
                    "fingerprint": keypair.fingerprint,
                    "web_public_jwk": web_keypair.public_jwk,
                    "web_fingerprint": web_keypair.fingerprint,
                    "mode": getattr(getattr(self.server, "omnidoer_config", None), "mode", "local_dev"),
                },
            )
            return
        if path == "/api/security-status":
            from omnidoer.omni_control.cloud import security_status

            self._send_json(HTTPStatus.OK, security_status(self.config))
            return
        if path == "/api/events":
            try:
                session = self._require_access()
                query = parse_qs(parsed_url.query)
                if query.get("stream", ["0"])[0] == "1":
                    snapshots = int(query.get("snapshots", ["12"])[0])
                    interval = float(query.get("interval", ["2"])[0])
                    self._send_sse_stream(store, session, snapshots=snapshots, interval=interval)
                else:
                    self._send_sse(self._sse_payload(store, session))
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid stream options"})
            return
        if path == "/api/devices":
            try:
                self._require_access()
                self._send_json(HTTPStatus.OK, [device.to_public_dict() for device in DeviceStore().list()])
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        if path == "/api/sessions":
            try:
                self._require_access()
                self._send_json(HTTPStatus.OK, [session.to_public_dict() for session in SessionStore().list()])
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        if path == "/api/requests":
            try:
                session = self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            self._send_json(HTTPStatus.OK, [request.to_public_dict() for request in self._visible_requests(store, session)])
            return
        if path == "/api/tasks":
            try:
                self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            self._send_json(HTTPStatus.OK, [task.to_public_dict() for task in TaskStore().list(include_completed=True)])
            return
        if path.startswith("/api/requests/"):
            try:
                session = self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            if path.endswith("/frame"):
                request_id = path.split("/")[-2]
                try:
                    request = self._get_request_for_session(store, request_id, session)
                    browser = get_browser_context(request.browser_context_id)
                    self._send_json(HTTPStatus.OK, start_stream(request_id, browser_controller=browser))
                except KeyError:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "request not found"})
                except PermissionError:
                    self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                except Exception as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
                return
            request_id = path.rsplit("/", 1)[-1]
            try:
                self._send_json(HTTPStatus.OK, self._get_request_for_session(store, request_id, session).to_public_dict())
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "request not found"})
            except PermissionError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        store = RequestStore()
        parts = path.strip("/").split("/")
        if path == "/api/pair":
            remote_key = f"pair:{self._remote_key()}"
            try:
                if not self._transport_allowed():
                    raise PermissionError("https proxy header required")
                if not self._origin_allowed():
                    raise PermissionError("origin rejected")
                PAIR_RATE_LIMIT.check(remote_key)
                body = self._read_json()
                result = pair_device(
                    code=str(body.get("code") or ""),
                    device_name=str(body.get("device_name") or "Control Client"),
                    device_public_key=str(body.get("device_public_key") or ""),
                )
                data = json.dumps(result.to_public_dict(), sort_keys=True).encode()
                self.send_response(HTTPStatus.CREATED)
                self._set_session_cookie(result.session.session_id, result.session_token)
                self.send_header("content-type", "application/json; charset=utf-8")
                self.send_header("cache-control", "no-store")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                PAIR_RATE_LIMIT.clear(remote_key)
            except Exception as exc:
                PAIR_RATE_LIMIT.record_failure(remote_key)
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": type(exc).__name__})
            return
        if path == "/api/tasks":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                task = TaskStore().create((self._read_json().get("text") or ""), source="control_client")
                self._send_json(HTTPStatus.CREATED, task.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/tasks/next":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                task = TaskStore().next_pending(claim=bool(body.get("claim", True)))
                if task is None:
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "status": "empty",
                            "secret_fields_allowed": False,
                            "submitted_to_openai_api_by_control_client": False,
                        },
                    )
                    return
                self._send_json(HTTPStatus.OK, task.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 4 and parts[:2] == ["api", "tasks"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            task_id, action = parts[2], parts[3]
            try:
                if action == "complete":
                    task = TaskStore().complete(task_id)
                elif action == "cancel":
                    task = TaskStore().cancel(task_id)
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                    return
                self._send_json(HTTPStatus.OK, task.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 4 and parts[:2] == ["api", "devices"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            device_id, action = parts[2], parts[3]
            if action != "revoke":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                return
            try:
                device = DeviceStore().revoke(device_id)
                revoked_sessions = SessionStore().revoke_for_device(device_id)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "revoked",
                        "device": device.to_public_dict(),
                        "revoked_sessions": [item.to_public_dict() for item in revoked_sessions],
                        "secret_exposed_to_model": False,
                    },
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 4 and parts[:2] == ["api", "sessions"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            session_id, action = parts[2], parts[3]
            if action != "revoke":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                return
            try:
                revoked = SessionStore().revoke(session_id)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "revoked",
                        "session": revoked.to_public_dict(),
                        "secret_exposed_to_model": False,
                    },
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 4 and parts[:2] == ["api", "requests"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            request_id, action = parts[2], parts[3]
            try:
                control_request = self._get_request_for_session(store, request_id, session)
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
                    envelope = body.get("envelope", body)
                    self._validate_envelope_for_session(envelope, control_request, session)
                    request = store.submit_ciphertext(request_id, envelope)
                elif action == "input":
                    request = control_request
                    browser = get_browser_context(request.browser_context_id)
                    if browser is None:
                        self._send_json(HTTPStatus.CONFLICT, {"error": "browser context is not connected"})
                        return
                    body = self._read_json()
                    self._send_json(HTTPStatus.OK, apply_input_event(request_id, event_from_dict(body), browser_controller=browser))
                    return
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                    return
                self._send_json(HTTPStatus.OK, request.to_public_dict())
            except PermissionError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_HEAD(self) -> None:
        super().do_HEAD()


def serve(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    public_url: str | None = None,
    cloud_direct: bool = False,
    tls_cert: str | None = None,
    tls_key: str | None = None,
    tls_self_signed_dev: bool = False,
    behind_reverse_proxy: bool = False,
    insecure_dev_public: bool = False,
) -> None:
    try:
        config = build_config(
            host=host,
            port=port,
            public_url=public_url,
            cloud_direct=cloud_direct,
            tls_cert=tls_cert,
            tls_key=tls_key,
            tls_self_signed_dev=tls_self_signed_dev,
            behind_reverse_proxy=behind_reverse_proxy,
            insecure_dev_public=insecure_dev_public,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    server = ThreadingHTTPServer((host, port), ControlHandler)
    server.omnidoer_config = config  # type: ignore[attr-defined]
    if tls_cert and tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(tls_cert, tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    elif tls_self_signed_dev:
        server.socket = _self_signed_context(host).wrap_socket(server.socket, server_side=True)
    if tls_self_signed_dev:
        print("WARNING: --tls-self-signed-dev is for localhost/test only. Use a real certificate or reverse proxy for Cloud Direct.")
    if insecure_dev_public:
        print("WARNING: --insecure-dev-public disables Cloud Direct HTTPS enforcement. Use only for temporary testing.")
    print(f"OmniDoer Control Service listening on {config.public_url} mode={config.mode}")
    server.serve_forever()

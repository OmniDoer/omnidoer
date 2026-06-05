"""Local HTML5/PWA Control Client server."""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
import json
import re
import socket
import ssl
import tempfile
import ipaddress
import threading
import time
import datetime as dt
from http.cookies import SimpleCookie
from importlib import resources
from pathlib import Path
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.auth import authenticate_session, authenticate_signed_session_request, pair_device
from omnidoer.omni_control.chat import DEFAULT_CHAT_SESSION_ID, ChatSessionStore, ChatStore, chat_cli_command_name, chat_text_is_cli_command, validate_chat_session_id
from omnidoer.omni_control.chat_uploads import (
    MAX_CHAT_UPLOAD_BYTES,
    ChatUploadStore,
    chat_upload_ttl_seconds,
    validate_uploaded_attachments,
)
from omnidoer.omni_control.cloud import ControlServiceConfig, build_config
from omnidoer.omni_control.csrf import CSRF_HEADER, verify_csrf
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.device_signing import (
    DEVICE_ID_HEADER,
    DEVICE_NONCE_HEADER,
    DEVICE_SESSION_ID_HEADER,
    DEVICE_SIG_HEADER,
    DEVICE_TS_HEADER,
)
from omnidoer.omni_control.rate_limit import RateLimiter
from omnidoer.omni_control.security_headers import apply_security_headers
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.runtime import record_control_service_runtime
from omnidoer.omni_control.pairing import PairingStore
from omnidoer.omni_control.secure_channel import load_or_create_keypair, load_or_create_web_keypair
from omnidoer.omni_control.sessions import CONTROL_SESSION_TTL_SECONDS, ControlSession, SessionStore
from omnidoer.omni_control.tasks import TaskStore
from omnidoer.omni_takeover.input_events import event_from_dict
from omnidoer.omni_takeover.relay import apply_input_event, start_stream
from omnidoer.omni_takeover.sessions import get_browser_context
from omnidoer.omni_takeover.stream import normalize_frame_profile


def static_root() -> Path:
    return Path(str(resources.files("omnidoer.omni_control") / "static"))


PAIR_RATE_LIMIT = RateLimiter(max_attempts=8, window_seconds=60, lockout_seconds=300)
CONTROL_MUTATION_RATE_LIMIT = RateLimiter(max_attempts=120, window_seconds=60, lockout_seconds=60)
CONSOLE_RESTART_REQUEST_TTL_SECONDS = 30 * 60
CONSOLE_RESTART_REQUEST_RENEW_WINDOW_SECONDS = 5 * 60
REQUEST_STREAM_DEFAULT_SNAPSHOTS = 1200
REQUEST_STREAM_MAX_SNAPSHOTS = 1200
REQUEST_STREAM_HEARTBEAT_SECONDS = 30.0
CHAT_STREAM_DEFAULT_SNAPSHOTS = 1200
CHAT_STREAM_MAX_SNAPSHOTS = 1200
CHAT_STREAM_HEARTBEAT_SECONDS = 30.0
QUOTA_STATUS_REFRESH_MIN_SECONDS = 120.0
BROWSER_CONTEXT_STREAM_DEFAULT_SNAPSHOTS = 1200
BROWSER_CONTEXT_STREAM_MAX_SNAPSHOTS = 1200
BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS = 30.0
BROWSER_FRAME_STREAM_DEFAULT_SNAPSHOTS = 1200
BROWSER_FRAME_STREAM_MAX_SNAPSHOTS = 1200
TAKEOVER_INPUT_RESULT_WAIT_MAX_SECONDS = 10.0
TLS_ACCEPT_PEEK_TIMEOUT_SECONDS = 2.0
CONTROL_SERVER_REQUEST_QUEUE_SIZE = 128
CLIENT_DISCONNECT_EXCEPTIONS = (BrokenPipeError, ConnectionResetError, ssl.SSLEOFError)
SENSITIVE_LOG_PATTERNS = [
    re.compile(r"(omnidoer_session=)[^;\s]+"),
    re.compile(r"(code=)[^&\s]+"),
    re.compile(r"(pairing_id=)[^&\s]+"),
    re.compile(r"(token=)[^&\s]+"),
]
STATUS_QUOTA_LABELS = (
    "Context window",
    "OmniDoer Usage limit",
    "OmniDoer limit",
    "GPT-5.3-Codex-Spark Usage limit",
    "GPT-5.3-Codex-Spark limit",
    "5h limit",
    "Weekly limit",
    "Daily limit",
    "Monthly limit",
    "Usage limit",
)
STATUS_BOX_CHARS = "│┃║╭╮╰╯┌┐└┘├┤┬┴┼─━═"


def _clean_terminal_status_line(line: str) -> str:
    text = line.strip()
    text = text.strip(STATUS_BOX_CHARS).strip()
    text = re.sub(r"\[[█░▓▒\s]+\]\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _looks_like_status_quota_line(text: str) -> bool:
    return any(text.startswith(f"{label}:") for label in STATUS_QUOTA_LABELS)


def _looks_like_status_continuation(text: str) -> bool:
    return text.startswith("(resets ") or text.startswith("resets ")


def _extract_latest_terminal_quota_lines(snapshot: str) -> list[str]:
    latest: list[str] = []
    current: list[str] = []
    for raw_line in snapshot.splitlines():
        if "│" not in raw_line:
            if current:
                latest = current
                current = []
            continue
        if re.match(r"^\s*(?:\d+\s+)?[+-]\s*│", raw_line):
            if current:
                latest = current
                current = []
            continue
        text = _clean_terminal_status_line(raw_line)
        if not text:
            if current:
                latest = current
                current = []
            continue
        if text.startswith("Context window:"):
            if current:
                latest = current
            current = [text]
            continue
        if not current:
            continue
        if _looks_like_status_quota_line(text) or _looks_like_status_continuation(text):
            if _looks_like_status_continuation(text) and current:
                current[-1] = f"{current[-1]} {text}"
            else:
                current.append(text)
            continue
        if current:
            latest = current
            current = []
    if current:
        latest = current
    return latest


def _extract_latest_plain_quota_lines(text: str) -> list[str]:
    latest: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`").lstrip("> ").strip()
        cleaned = _clean_terminal_status_line(line)
        if cleaned == "Quota:":
            if current:
                latest = current
            current = []
            continue
        if _looks_like_status_quota_line(cleaned):
            if not current or cleaned.startswith("Context window:"):
                if current:
                    latest = current
                current = [cleaned]
            else:
                current.append(cleaned)
            continue
        if _looks_like_status_continuation(cleaned) and current:
            current[-1] = f"{current[-1]} {cleaned}"
            continue
        if current:
            latest = current
            current = []
    if current:
        latest = current
    return latest


def _quota_percent_left(line: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)%\s+left", line)
    if not match:
        return None
    return float(match.group(1))


def _terminal_quota_summary(lines: list[str]) -> dict[str, object]:
    summary: dict[str, object] = {"lines": lines}
    for line in lines:
        percent = _quota_percent_left(line)
        if percent is None:
            continue
        if line.startswith(("OmniDoer Usage limit:", "OmniDoer limit:")):
            summary["omnidoer_percent_left"] = percent
        elif line.startswith("5h limit:"):
            summary.setdefault("codex_5h_percent_left", percent)
        elif line.startswith("Weekly limit:"):
            summary.setdefault("codex_weekly_percent_left", percent)
    return summary


def _quota_summary_has_codex_percentages(summary: dict[str, object] | None) -> bool:
    if not summary:
        return False
    return "codex_5h_percent_left" in summary and "codex_weekly_percent_left" in summary


def _recent_chat_quota_summary() -> dict[str, object] | None:
    candidates: list[tuple[float, str]] = []
    store = ChatStore()
    for record in store.list_records(limit=140):
        if record.text:
            candidates.append((float(record.created_at or 0), record.text))
    for message in store.list(limit=80):
        if message.text:
            candidates.append((float(message.updated_at or message.created_at or 0), message.text))
    for _, text in sorted(candidates, key=lambda item: item[0], reverse=True):
        lines = _extract_latest_terminal_quota_lines(text) or _extract_latest_plain_quota_lines(text)
        if not lines:
            continue
        summary = _terminal_quota_summary(lines)
        if _quota_summary_has_codex_percentages(summary):
            return summary
    return None


def _active_terminal_quota_summary(chat_thread_id: str | None) -> dict[str, object] | None:
    if not chat_thread_id:
        return None
    from omnidoer.omni_control.tui_legacy_relay import capture_tmux_pane, find_tmux_pane_for_thread, list_tmux_panes

    pane = find_tmux_pane_for_thread(chat_thread_id)
    panes = [pane] if pane is not None else [
        candidate for candidate in list_tmux_panes() if candidate.current_command in {"codex", "omnidoer"}
    ]
    for candidate in panes:
        snapshot = capture_tmux_pane(candidate.pane_id, line_count=1000)
        lines = _extract_latest_terminal_quota_lines(snapshot)
        if not lines:
            continue
        summary = _terminal_quota_summary(lines)
        if _quota_summary_has_codex_percentages(summary):
            summary["source"] = "tmux"
            summary["pane_id"] = candidate.pane_id
            return summary
    return None


def _active_terminal_quota_text(chat_thread_id: str | None) -> str | None:
    summary = _active_terminal_quota_summary(chat_thread_id)
    if not summary:
        return None
    lines = [str(line) for line in summary.get("lines", [])]
    return "\n".join(["Quota:"] + lines)


class TLSAwareThreadingHTTPServer(ThreadingHTTPServer):
    """Accept TLS and accidental plaintext HTTP on a direct-TLS listener."""

    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = CONTROL_SERVER_REQUEST_QUEUE_SIZE

    def __init__(
        self,
        server_address,
        request_handler_class,
        bind_and_activate: bool = True,
        *,
        tls_context: ssl.SSLContext | None = None,
    ):
        self.omnidoer_tls_context = tls_context
        super().__init__(server_address, request_handler_class, bind_and_activate=bind_and_activate)

    def get_request(self):
        conn, addr = self.socket.accept()
        context = self.omnidoer_tls_context
        if context is None:
            return conn, addr
        previous_timeout = conn.gettimeout()
        conn.settimeout(getattr(self, "omnidoer_tls_accept_peek_timeout_seconds", TLS_ACCEPT_PEEK_TIMEOUT_SECONDS))
        try:
            first = conn.recv(1, socket.MSG_PEEK)
            if not first:
                raise OSError("client closed before TLS sniff")
            if first[0] == 0x16:
                conn = context.wrap_socket(conn, server_side=True)
            conn.settimeout(previous_timeout)
        except (OSError, ssl.SSLError):
            conn.close()
            raise
        return conn, addr


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


def console_restart_request_details(
    *,
    public_url: str,
    chat_thread_id: str | None,
    detached_thread_resume_allowed: bool = False,
) -> dict:
    from omnidoer.omni_control.chat_runner import (
        active_tui_process_bridge_status,
        active_mcp_sidecar_status,
        control_chat_sync_diagnostics,
        live_tui_bridge_active,
        live_tui_session_active,
        native_console_bridge_install_status,
        tui_bridge_heartbeat_status,
        tui_restart_command,
    )
    from omnidoer.omni_control.tui_legacy_relay import legacy_tui_relay_status

    bridge_heartbeat = tui_bridge_heartbeat_status(chat_thread_id)
    tui_bridge_active = live_tui_bridge_active(chat_thread_id)
    tui_session_active = live_tui_session_active(chat_thread_id)
    legacy_relay = legacy_tui_relay_status(chat_thread_id) if chat_thread_id and not tui_bridge_active else {"active": False}
    install_status = native_console_bridge_install_status()
    active_process = active_tui_process_bridge_status(chat_thread_id)
    mcp_sidecar = active_mcp_sidecar_status(chat_thread_id)
    diagnostics = control_chat_sync_diagnostics(
        thread_id=chat_thread_id,
        tui_bridge_active=tui_bridge_active,
        tui_session_active=tui_session_active,
        legacy_relay=legacy_relay,
        install_status=install_status,
        active_process_bridge=active_process,
        mcp_sidecar=mcp_sidecar,
        bridge_heartbeat_age_seconds=bridge_heartbeat.get("age_seconds"),
        bridge_heartbeat=bridge_heartbeat,
        detached_thread_resume_allowed=detached_thread_resume_allowed,
    )
    browser_relay_restart = bool(
        diagnostics.get("requires_restart_for_browser_takeover_relay")
        and not diagnostics.get("requires_restart_for_native_sync")
    )
    return {
        "thread_id": chat_thread_id,
        "restart_purpose": "browser_takeover_relay" if browser_relay_restart else "current_session_sync",
        "restart_command": tui_restart_command(chat_thread_id),
        "current_state": diagnostics.get("state"),
        "native_sync_active": diagnostics.get("native_sync_active"),
        "current_cli_context_attached": diagnostics.get("current_cli_context_attached"),
        "requires_restart_for_native_sync": diagnostics.get("requires_restart_for_native_sync"),
        "requires_restart_for_browser_takeover_relay": diagnostics.get("requires_restart_for_browser_takeover_relay"),
        "restart_current_console_available": diagnostics.get("restart_current_console_available"),
        "restart_browser_takeover_relay_available": diagnostics.get("restart_browser_takeover_relay_available"),
        "activation_action": diagnostics.get("activation_action"),
        "active_cli_pid": active_process.get("pid"),
        "active_cli_binary_reason": active_process.get("reason"),
        "mcp_sidecar": mcp_sidecar,
        "bridge_heartbeat": bridge_heartbeat,
        "legacy_transport": legacy_relay.get("transport"),
        "legacy_pane_id": legacy_relay.get("pane_id"),
        "after_approval": (
            "Restart the active Codex TUI in its tmux pane, keep the same thread, and load a fresh MCP sidecar for browser takeover relay."
            if browser_relay_restart
            else "Restart the active Codex TUI in its tmux pane, keep the same thread, and load the installed native bridge."
        ),
    }


def console_restart_request_available(details: dict) -> bool:
    browser_relay_restart = bool(
        details.get("thread_id")
        and details.get("requires_restart_for_browser_takeover_relay")
        and details.get("restart_browser_takeover_relay_available")
    )
    return bool(
        browser_relay_restart
        or (
            details.get("thread_id")
            and details.get("requires_restart_for_native_sync")
            and details.get("restart_current_console_available")
            and details.get("activation_action") == "restart_current_console"
        )
    )


def create_or_renew_console_restart_request(
    store: RequestStore,
    *,
    public_url: str,
    details: dict,
    session: ControlSession | None = None,
    requires_pairing: bool = False,
) -> tuple[object, bool]:
    chat_thread_id = str(details.get("thread_id") or "")
    if not chat_thread_id:
        raise ValueError("chat_thread_not_bound")
    restart_purpose = str(details.get("restart_purpose") or "")
    browser_relay_restart = restart_purpose == "browser_takeover_relay" or bool(
        details.get("requires_restart_for_browser_takeover_relay") and not details.get("requires_restart_for_native_sync")
    )
    action_summary = (
        f"Restart current Agent for browser takeover relay on {chat_thread_id}"
        if browser_relay_restart
        else f"Enable current session sync for {chat_thread_id}"
    )
    now = time.time()
    for existing in store.list():
        existing_details = existing.structured_details or {}
        session_allowed = not requires_pairing or not existing.allowed_device_id or (
            session is not None and existing.allowed_device_id == session.device_id
        )
        if (
            existing.request_type == "console_restart"
            and existing.status == "pending"
            and existing_details.get("thread_id") == chat_thread_id
            and session_allowed
        ):
            should_update = False
            if existing.structured_details != details:
                existing.structured_details = details
                should_update = True
            if existing.action_summary != action_summary:
                existing.action_summary = action_summary
                should_update = True
            if existing.expires_at - now < CONSOLE_RESTART_REQUEST_RENEW_WINDOW_SECONDS:
                existing.expires_at = now + CONSOLE_RESTART_REQUEST_TTL_SECONDS
                should_update = True
            if should_update:
                existing = store.update(existing)
            return existing, True
    request = store.create(
        "console_restart",
        origin="omnidoer://control",
        top_level_url=public_url,
        action_summary=action_summary,
        risk_level="high",
        ttl_seconds=CONSOLE_RESTART_REQUEST_TTL_SECONDS,
        # Current-session sync is a server-level operation. Any paired
        # Control Client may review it, but approval still requires the
        # explicit high-risk confirmation payload.
        allowed_device_id=None,
        structured_details=details,
    )
    return request, False


def cancel_obsolete_console_restart_requests(
    store: RequestStore,
    *,
    chat_thread_id: str | None,
    session: ControlSession | None = None,
    requires_pairing: bool = False,
) -> list[object]:
    if not chat_thread_id:
        return []
    cancelled = []
    for existing in store.list():
        existing_details = existing.structured_details or {}
        session_allowed = not requires_pairing or not existing.allowed_device_id or (
            session is not None and existing.allowed_device_id == session.device_id
        )
        if (
            existing.request_type == "console_restart"
            and existing.status == "pending"
            and existing_details.get("thread_id") == chat_thread_id
            and session_allowed
        ):
            cancelled.append(store.cancel(existing.request_id, reason="restart_no_longer_required"))
    return cancelled


def ensure_current_session_sync_request(
    store: RequestStore,
    *,
    public_url: str,
    chat_thread_id: str | None,
    detached_thread_resume_allowed: bool = False,
    session: ControlSession | None = None,
    requires_pairing: bool = False,
):
    if requires_pairing and session is None:
        return None
    details = console_restart_request_details(
        public_url=public_url,
        chat_thread_id=chat_thread_id,
        detached_thread_resume_allowed=detached_thread_resume_allowed,
    )
    if not console_restart_request_available(details):
        cancel_obsolete_console_restart_requests(
            store,
            chat_thread_id=chat_thread_id,
            session=session,
            requires_pairing=requires_pairing,
        )
        return None
    request, _ = create_or_renew_console_restart_request(
        store,
        public_url=public_url,
        details=details,
        session=session,
        requires_pairing=requires_pairing,
    )
    return request


def start_current_session_sync_request_maintainer(
    *,
    config: ControlServiceConfig,
    chat_thread_id: str | None,
    detached_thread_resume_allowed: bool = False,
    interval_seconds: float = 60.0,
) -> threading.Thread | None:
    if not chat_thread_id:
        return None

    def maintain() -> None:
        while True:
            try:
                ensure_current_session_sync_request(
                    RequestStore(),
                    public_url=config.public_url,
                    chat_thread_id=chat_thread_id,
                    detached_thread_resume_allowed=detached_thread_resume_allowed,
                    requires_pairing=False,
                )
            except Exception:
                pass
            time.sleep(max(5.0, interval_seconds))

    thread = threading.Thread(target=maintain, name="omnidoer-current-session-sync-request", daemon=True)
    thread.start()
    return thread


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
        try:
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except CLIENT_DISCONNECT_EXCEPTIONS:
            self.close_connection = True

    def _send_pwa_index(self) -> None:
        data = (static_root() / "index.html").read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _plain_http_on_direct_tls_port(self) -> bool:
        return bool(getattr(self.server, "omnidoer_direct_tls", False)) and not isinstance(self.request, ssl.SSLSocket)

    def _send_https_required(self, *, include_body: bool = True) -> None:
        parsed = urlparse(self.path)
        if parsed.query:
            body = b"Use the HTTPS OmniDoer Control Service URL. Pairing URLs are not redirected from plaintext HTTP.\n"
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(body) if include_body else 0))
            self.end_headers()
            if include_body:
                self.wfile.write(body)
            return
        target = f"{self.config.public_url.rstrip('/')}{parsed.path or '/'}"
        body = f"Use HTTPS: {target}\n".encode()
        self.send_response(HTTPStatus.PERMANENT_REDIRECT)
        self.send_header("location", target)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(body) if include_body else 0))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def end_headers(self) -> None:
        apply_security_headers(self.send_header)
        super().end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def _read_multipart_files(self) -> list[dict]:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return []
        if length > MAX_CHAT_UPLOAD_BYTES:
            raise ValueError("upload is too large")
        content_type = self.headers.get("content-type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("multipart/form-data required")
        body = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
        )
        files = []
        for part in message.iter_parts():
            filename = part.get_filename()
            if not filename:
                continue
            payload = part.get_payload(decode=True) or b""
            files.append(
                {
                    "filename": filename,
                    "content": payload,
                    "content_type": part.get_content_type(),
                }
            )
        return files

    def _chat_upload_ttl_seconds(self) -> int:
        return int(getattr(self.server, "omnidoer_chat_upload_ttl_seconds", chat_upload_ttl_seconds()))

    @property
    def config(self) -> ControlServiceConfig:
        return getattr(self.server, "omnidoer_config", build_config(host="127.0.0.1", port=8787))

    def _sse_payload(self, store: RequestStore, session: ControlSession | None) -> dict:
        return {"requests": [request.to_public_dict() for request in self._visible_requests(store, session)]}

    def _request_payload_fingerprint(self, payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _chat_session_id_from_query(self, query: dict[str, list[str]]) -> str:
        value = query.get("session_id", [None])[0]
        if value:
            return validate_chat_session_id(value)
        return ChatSessionStore().active_session_id()

    def _chat_payload(self, *, limit: int = 200, after_sequence: int | None = None, session_id: str | None = None, compact: bool = False) -> dict:
        resolved_session_id = validate_chat_session_id(session_id or ChatSessionStore().active_session_id())
        store = ChatStore(session_id=resolved_session_id)
        if not compact:
            store.prune_now()
        resolved_limit = max(1, min(limit, 40 if compact else 200))
        messages = store.list(limit=resolved_limit)
        records = store.list_records(limit=resolved_limit, after_sequence=after_sequence)
        if compact:
            return {
                "messages": [message.to_public_dict() for message in messages],
                "records": [record.to_public_dict() for record in records],
                "session_id": resolved_session_id,
                "streaming": True,
                "compact": True,
                "retention": {"days": 3, "max_records": 140},
                "control_client_calls_model": False,
            }
        chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
        from omnidoer.omni_control.tui_legacy_relay import legacy_tui_terminal_snapshot

        return {
            "messages": [message.to_public_dict() for message in messages],
            "records": [record.to_public_dict() for record in records],
            "session_id": resolved_session_id,
            "sessions": ChatSessionStore().list(),
            "streaming": True,
            "terminal": legacy_tui_terminal_snapshot(chat_thread_id),
            "retention": {"days": 3, "max_records": 140},
            "uploads": {
                "directory": str(ChatUploadStore().directory),
                "ttl_seconds": self._chat_upload_ttl_seconds(),
            },
            "control_client_calls_model": False,
        }

    def _chat_payload_fingerprint(self, payload: dict) -> str:
        messages = payload.get("messages") or []
        records = payload.get("records") or []
        terminal = payload.get("terminal") or {}
        last_message = messages[-1] if messages else {}
        last_record = records[-1] if records else {}
        terminal_text = str(terminal.get("text") or "") if isinstance(terminal, dict) else ""
        fingerprint = [
            len(messages),
            last_message.get("sequence"),
            last_message.get("status"),
            last_message.get("updated_at"),
            len(records),
            last_record.get("sequence"),
            last_record.get("record_type"),
            last_record.get("created_at"),
            terminal.get("available") if isinstance(terminal, dict) else False,
            len(terminal_text),
            terminal_text[-240:],
        ]
        return json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)

    def _stream_heartbeat_payload(self) -> dict:
        return {
            "status": "ok",
            "secret_exposed_to_model": False,
            "control_client_calls_model": False,
        }

    def _browser_context_payload(self) -> dict:
        from omnidoer.omni_takeover.cross_process import list_contexts

        return {
            "contexts": list_contexts(),
            "streaming": True,
            "secret_exposed_to_model": False,
        }

    def _browser_context_payload_fingerprint(self, payload: dict) -> str:
        contexts = payload.get("contexts") or []
        fingerprint = [
            [
                item.get("browser_context_id"),
                item.get("current_url"),
                item.get("origin"),
                item.get("updated_at"),
                item.get("active"),
            ]
            for item in contexts
        ]
        return json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)

    def _send_sse(self, payload: dict, *, event: str = "requests") -> None:
        from omnidoer.omni_control.websocket import sse_event

        data = sse_event(event, payload)
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
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, REQUEST_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._sse_payload(store, session)
            fingerprint = self._request_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= REQUEST_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(sse_event("heartbeat", self._stream_heartbeat_payload()))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(sse_event("requests", payload))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _open_websocket(self):
        from omnidoer.omni_control.websocket import decode_device_auth_subprotocol, websocket_accept_key, websocket_text_frame

        client_key = self.headers.get("sec-websocket-key")
        if not client_key:
            raise PermissionError("websocket key required")
        protocol = decode_device_auth_subprotocol(self.headers.get("sec-websocket-protocol"))
        self.send_response(HTTPStatus.SWITCHING_PROTOCOLS)
        self.send_header("upgrade", "websocket")
        self.send_header("connection", "Upgrade")
        self.send_header("sec-websocket-accept", websocket_accept_key(client_key))
        if protocol and protocol.get("subprotocol"):
            self.send_header("sec-websocket-protocol", protocol["subprotocol"])
        self.end_headers()
        return websocket_text_frame

    def _send_websocket_stream(self, store: RequestStore, session: ControlSession | None, *, snapshots: int, interval: float) -> None:
        websocket_text_frame = self._open_websocket()
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, REQUEST_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._sse_payload(store, session)
            fingerprint = self._request_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= REQUEST_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(websocket_text_frame({"event": "heartbeat", "data": self._stream_heartbeat_payload()}))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(websocket_text_frame({"event": "requests", "data": payload}))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _send_chat_sse_stream(self, *, snapshots: int, interval: float, limit: int, after_sequence: int | None, session_id: str | None = None, compact: bool = False) -> None:
        from omnidoer.omni_control.websocket import sse_event

        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("connection", "close")
        self.end_headers()
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, CHAT_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._chat_payload(limit=limit, after_sequence=after_sequence, session_id=session_id, compact=compact)
            fingerprint = self._chat_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= CHAT_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(sse_event("heartbeat", self._stream_heartbeat_payload()))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(sse_event("chat", payload))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _send_chat_websocket_stream(self, *, snapshots: int, interval: float, limit: int, after_sequence: int | None, session_id: str | None = None, compact: bool = False) -> None:
        websocket_text_frame = self._open_websocket()
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, CHAT_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._chat_payload(limit=limit, after_sequence=after_sequence, session_id=session_id, compact=compact)
            fingerprint = self._chat_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= CHAT_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(websocket_text_frame({"event": "heartbeat", "data": self._stream_heartbeat_payload()}))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(websocket_text_frame({"event": "chat", "data": payload}))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _send_takeover_frame_websocket_stream(
        self,
        store: RequestStore,
        session: ControlSession | None,
        request_id: str,
        *,
        snapshots: int,
        interval: float,
        frame_profile: str,
    ) -> None:
        self._get_request_for_session(store, request_id, session)
        websocket_text_frame = self._open_websocket()
        for index in range(max(1, min(snapshots, BROWSER_FRAME_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            request = self._get_request_for_session(store, request_id, session)
            frame = self._takeover_request_frame(request_id, request, frame_profile=frame_profile)
            if frame is not None:
                store.record_takeover_frame(request_id, frame)
            self.wfile.write(
                websocket_text_frame(
                    {
                        "event": "takeover_frame",
                        "request_id": request_id,
                        "data": frame or {},
                        "error": None if frame else "browser_frame_unavailable",
                        "secret_exposed_to_model": False,
                    }
                )
            )
            self.wfile.flush()
        self.close_connection = True

    def _send_browser_context_sse_stream(self, *, snapshots: int, interval: float) -> None:
        from omnidoer.omni_control.websocket import sse_event

        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("connection", "close")
        self.end_headers()
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, BROWSER_CONTEXT_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._browser_context_payload()
            fingerprint = self._browser_context_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(sse_event("heartbeat", self._stream_heartbeat_payload()))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(sse_event("browser_contexts", payload))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _send_browser_context_websocket_stream(self, *, snapshots: int, interval: float) -> None:
        websocket_text_frame = self._open_websocket()
        last_fingerprint = ""
        last_write_at = 0.0
        for index in range(max(1, min(snapshots, BROWSER_CONTEXT_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            payload = self._browser_context_payload()
            fingerprint = self._browser_context_payload_fingerprint(payload)
            if index and fingerprint == last_fingerprint:
                now = time.monotonic()
                if now - last_write_at >= BROWSER_CONTEXT_STREAM_HEARTBEAT_SECONDS:
                    self.wfile.write(websocket_text_frame({"event": "heartbeat", "data": self._stream_heartbeat_payload()}))
                    self.wfile.flush()
                    last_write_at = now
                continue
            last_fingerprint = fingerprint
            self.wfile.write(websocket_text_frame({"event": "browser_contexts", "data": payload}))
            self.wfile.flush()
            last_write_at = time.monotonic()
        self.close_connection = True

    def _browser_context_frame(self, context_id: str, *, frame_profile: str) -> dict | None:
        browser = get_browser_context(context_id)
        if browser is not None:
            return browser.takeover_frame(frame_profile=frame_profile)
        from omnidoer.omni_takeover.cross_process import read_frame

        return read_frame(context_id)

    def _takeover_request_frame(self, request_id: str, request, *, frame_profile: str) -> dict | None:
        browser = get_browser_context(request.browser_context_id)
        if browser is not None:
            return start_stream(request_id, browser_controller=browser, frame_profile=frame_profile)
        if request.browser_context_id:
            from omnidoer.omni_takeover.cross_process import read_frame

            return read_frame(request.browser_context_id)
        return None

    def _send_browser_context_frame_websocket_stream(
        self,
        context_id: str,
        *,
        snapshots: int,
        interval: float,
        frame_profile: str,
    ) -> None:
        websocket_text_frame = self._open_websocket()
        for index in range(max(1, min(snapshots, BROWSER_FRAME_STREAM_MAX_SNAPSHOTS))):
            if index:
                time.sleep(max(0.0, min(interval, 10.0)))
            frame = self._browser_context_frame(context_id, frame_profile=frame_profile)
            payload = {
                "event": "browser_context_frame",
                "browser_context_id": context_id,
                "data": frame or {},
                "error": None if frame else "browser_frame_unavailable",
            }
            self.wfile.write(websocket_text_frame(payload))
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
        if self.config.mode == "cloud_direct":
            from omnidoer.omni_control.websocket import decode_device_auth_subprotocol

            protocol = decode_device_auth_subprotocol(self.headers.get("sec-websocket-protocol"))
            device_id = self.headers.get(DEVICE_ID_HEADER, "")
            signed_session_id = self.headers.get(DEVICE_SESSION_ID_HEADER, "")
            timestamp = self.headers.get(DEVICE_TS_HEADER, "")
            nonce = self.headers.get(DEVICE_NONCE_HEADER, "")
            signature = self.headers.get(DEVICE_SIG_HEADER, "")
            if protocol:
                device_id = protocol["device_id"]
                signed_session_id = protocol.get("session_id", signed_session_id)
                timestamp = protocol["timestamp"]
                nonce = protocol["nonce"]
                signature = protocol["signature"]
            session_id = session_id or signed_session_id
            if not session_id:
                raise PermissionError("session required")
            return authenticate_signed_session_request(
                session_id=session_id,
                session_token=token or "",
                device_id=device_id,
                method=self.command,
                path=urlparse(self.path).path,
                timestamp=timestamp,
                nonce=nonce,
                signature=signature,
                device_store=DeviceStore(),
                session_store=SessionStore(),
                allow_missing_session_token=True,
            )
        if not session_id or not token:
            raise PermissionError("session required")
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

    def _console_restart_request_available(self, details: dict) -> bool:
        return console_restart_request_available(details)

    def _ensure_current_session_sync_request(self, store: RequestStore, session: ControlSession | None):
        return ensure_current_session_sync_request(
            store,
            public_url=self.config.public_url,
            chat_thread_id=getattr(self.server, "omnidoer_chat_thread_id", None),
            detached_thread_resume_allowed=bool(getattr(self.server, "omnidoer_chat_allow_detached_thread_resume", False)),
            session=session,
            requires_pairing=self._requires_pairing(),
        )

    def _visible_requests(self, store: RequestStore, session: ControlSession | None):
        self._ensure_current_session_sync_request(store, session)
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

    def _try_deliver_chat_to_live_console(self, message_id: str) -> dict:
        chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
        if not chat_thread_id:
            return {"attempted": False, "reason": "chat_thread_not_bound", "secret_exposed_to_model": False}
        from omnidoer.omni_control.chat_runner import live_tui_bridge_active

        if live_tui_bridge_active(chat_thread_id):
            return {"attempted": False, "reason": "native_bridge_active", "secret_exposed_to_model": False}
        from omnidoer.omni_control.tui_legacy_relay import (
            LegacyTuiRelay,
            legacy_tui_relay_status,
        )

        status = legacy_tui_relay_status(chat_thread_id)
        if not status.get("active"):
            return {
                "attempted": False,
                "reason": str(status.get("reason") or "legacy_relay_unavailable"),
                "legacy_tui_relay": status,
            }
        relay = LegacyTuiRelay(thread_id=chat_thread_id)
        try:
            message = ChatStore().get(message_id)
        except KeyError:
            message = None
        delivered = relay.run_message(message_id) if message is not None else False
        return {
            "attempted": True,
            "delivered": bool(delivered),
            "message_id": message_id,
            "thread_id": chat_thread_id,
            "transport": status.get("transport") or "tmux",
            "pane_id": status.get("pane_id"),
            "secret_exposed_to_model": False,
        }

    def _queue_agent_instruction(
        self,
        *,
        text: str,
        client_message_id: str,
        session: ControlSession | None,
    ) -> dict:
        chat_store = ChatStore()
        message = chat_store.append(
            role="user",
            text=text,
            source="control_client",
            author_device_id=session.device_id if session else None,
            client_message_id=client_message_id,
        )
        delivery = self._try_deliver_chat_to_live_console(message.message_id)
        try:
            payload = chat_store.get(message.message_id).to_public_dict()
        except KeyError:
            payload = message.to_public_dict()
        return {
            "message": payload,
            "live_console_delivery": delivery,
            "secret_exposed_to_model": False,
        }

    def _control_client_status_text(self) -> str:
        from omnidoer.omni_control.chat_runner import (
            active_mcp_sidecar_status,
            active_tui_process_bridge_status,
            live_tui_bridge_active,
            native_console_bridge_install_status,
            tui_bridge_heartbeat_status,
        )

        chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
        bridge_heartbeat = tui_bridge_heartbeat_status(chat_thread_id)
        active_process = active_tui_process_bridge_status(chat_thread_id)
        native_bridge = native_console_bridge_install_status()
        mcp_sidecar = active_mcp_sidecar_status(chat_thread_id)
        browser_takeover = (mcp_sidecar.get("browser_takeover") or {}) if isinstance(mcp_sidecar, dict) else {}
        bridge_active = live_tui_bridge_active(chat_thread_id)
        restart_required = bool(
            active_process.get("restart_required")
            or mcp_sidecar.get("restart_required")
            or not native_bridge.get("ready")
        )
        heartbeat_age = bridge_heartbeat.get("age_seconds")
        heartbeat_label = f"{heartbeat_age:.1f}s" if isinstance(heartbeat_age, (int, float)) else "unknown"
        lines = [
            "OmniDoer status",
            f"Mode: {self.config.mode}",
            f"Control service: ok",
            f"Public URL: {self.config.public_url}",
            f"Thread: {chat_thread_id or 'not bound'}",
            f"CLI bridge: {'active' if bridge_active else bridge_heartbeat.get('reason') or 'inactive'}",
            f"Bridge heartbeat: {heartbeat_label}",
            f"Native console bridge: {native_bridge.get('reason') or 'unknown'}",
            f"Active console process: {active_process.get('reason') or 'unknown'}",
            f"MCP sidecar: {mcp_sidecar.get('reason') or 'unknown'}",
            f"Browser takeover relay: {browser_takeover.get('state') or browser_takeover.get('reason') or 'unknown'}",
            f"Restart required: {'yes' if restart_required else 'no'}",
            "Secret exposure: false",
            "Model submission: false",
        ]
        quota_text = _active_terminal_quota_text(chat_thread_id)
        if quota_text:
            lines.extend(["", quota_text])
        return "\n".join(lines)

    def _maybe_queue_quota_status_refresh(
        self,
        *,
        chat_thread_id: str | None,
        tui_bridge_active: bool,
        quota_summary: dict[str, object],
    ) -> dict[str, object]:
        if _quota_summary_has_codex_percentages(quota_summary):
            return {"attempted": False, "reason": "quota_available"}
        if not chat_thread_id:
            return {"attempted": False, "reason": "chat_thread_not_bound"}
        if not tui_bridge_active:
            return {"attempted": False, "reason": "native_bridge_inactive"}

        now = time.time()
        last_requested = float(getattr(self.server, "omnidoer_last_quota_status_request_at", 0.0) or 0.0)
        if now - last_requested < QUOTA_STATUS_REFRESH_MIN_SECONDS:
            return {
                "attempted": False,
                "reason": "rate_limited",
                "retry_after_seconds": max(0.0, QUOTA_STATUS_REFRESH_MIN_SECONDS - (now - last_requested)),
            }

        from omnidoer.omni_control.tui_legacy_relay import inject_text_into_tmux_pane, list_tmux_panes

        pane = next((candidate for candidate in list_tmux_panes() if candidate.current_command in {"codex", "omnidoer"}), None)
        if pane is None:
            return {"attempted": False, "reason": "tmux_pane_not_found"}
        try:
            inject_text_into_tmux_pane(pane.pane_id, "/status")
        except Exception as exc:
            return {"attempted": False, "reason": type(exc).__name__}
        setattr(self.server, "omnidoer_last_quota_status_request_at", now)
        return {
            "attempted": True,
            "reason": "tmux_status_requested",
            "pane_id": pane.pane_id,
            "thread_id": chat_thread_id,
        }

    def _control_client_help_text(self) -> str:
        return "\n".join(
            [
                "OmniDoer CLI commands",
                "/status - show runtime, bridge, and safety status",
                "/model - mobile model switching is not available yet; use the terminal console model picker",
                "/quota or /usage - alias for /status in the mobile Control Client",
                "/help - show this command list",
                "Other slash commands are delivered to the active OmniDoer console bridge, not to the model.",
            ]
        )

    def _control_client_model_text(self) -> str:
        return "\n".join(
            [
                "OmniDoer model selection",
                "/model opens an interactive TUI picker in the terminal console.",
                "The mobile Control Client cannot render that picker yet, so this command was handled locally instead of opening a hidden SSH-side menu.",
                "Use the terminal console for model changes until the mobile model selector is implemented.",
                "Secret exposure: false",
                "Model submission: false",
            ]
        )

    def _active_cli_accepts_remote_slash_commands(self) -> tuple[bool, str]:
        from omnidoer.omni_control.chat_runner import (
            active_tui_process_bridge_status,
            live_tui_bridge_active,
            native_console_bridge_install_status,
        )

        chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
        if not chat_thread_id:
            return False, "chat_thread_not_bound"
        if not live_tui_bridge_active(chat_thread_id):
            return False, "native_bridge_inactive"
        native_bridge = native_console_bridge_install_status()
        if not native_bridge.get("ready"):
            return False, str(native_bridge.get("reason") or "native_bridge_not_ready")
        active_process = active_tui_process_bridge_status(chat_thread_id)
        if not active_process.get("active"):
            return False, str(active_process.get("reason") or "active_console_not_found")
        if active_process.get("restart_required"):
            return False, str(active_process.get("reason") or "active_console_restart_required")
        return True, "native_bridge_ready"

    def _append_control_cli_response(
        self,
        *,
        text: str,
        client_message_id: str | None,
        session: ControlSession | None,
        command: str,
        response_text: str,
        delivery_reason: str,
    ) -> dict:
        chat_store = ChatStore()
        user = chat_store.append(
            role="user",
            text=text,
            status="completed",
            source="control_client",
            author_device_id=session.device_id if session else None,
            client_message_id=client_message_id,
        )
        assistant = chat_store.append(
            role="assistant",
            text=response_text,
            status="completed",
            source="control_service",
            reply_to_message_id=user.message_id,
        )
        payload = user.to_public_dict()
        payload["live_console_delivery"] = {
            "attempted": False,
            "delivered": True,
            "reason": delivery_reason,
            "command": f"/{command}",
            "secret_exposed_to_model": False,
            "submitted_to_model": False,
        }
        payload["cli_command_response"] = assistant.to_public_dict()
        return payload

    def _handle_control_cli_command(
        self,
        *,
        text: str,
        client_message_id: str | None,
        session: ControlSession | None,
    ) -> dict | None:
        if not (str(client_message_id or "").startswith("control_cli_") or chat_text_is_cli_command(text)):
            return None
        command = chat_cli_command_name(text)
        if command == "model":
            return self._append_control_cli_response(
                text=text,
                client_message_id=client_message_id,
                session=session,
                command=command,
                response_text=self._control_client_model_text(),
                delivery_reason="handled_by_control_service",
            )
        if command not in {"status", "quota", "usage", "help"}:
            bridge_ready, reason = self._active_cli_accepts_remote_slash_commands()
            if bridge_ready:
                return None
            response_text = (
                f"CLI command /{command or 'unknown'} was not sent to the model. "
                f"The active OmniDoer console bridge is not ready for remote slash commands: {reason}. "
                "Restart the active console to run this command through the CLI."
            )
            return self._append_control_cli_response(
                text=text,
                client_message_id=client_message_id,
                session=session,
                command=command or "unknown",
                response_text=response_text,
                delivery_reason=reason,
            )
        response_text = self._control_client_help_text() if command == "help" else self._control_client_status_text()
        return self._append_control_cli_response(
            text=text,
            client_message_id=client_message_id,
            session=session,
            command=command,
            response_text=response_text,
            delivery_reason="handled_by_control_service",
        )

    def _safe_queue_agent_instruction(
        self,
        *,
        text: str,
        client_message_id: str,
        session: ControlSession | None,
    ) -> dict:
        try:
            return self._queue_agent_instruction(
                text=text,
                client_message_id=client_message_id,
                session=session,
            )
        except Exception as exc:
            return {
                "error": type(exc).__name__,
                "client_message_id": client_message_id,
                "secret_exposed_to_model": False,
            }

    def _restart_console_bridge(self) -> dict:
        chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
        from omnidoer.omni_control.chat_runner import tui_restart_command
        from omnidoer.omni_control.tui_legacy_relay import restart_tmux_pane_for_bridge

        result = restart_tmux_pane_for_bridge(
            chat_thread_id,
            restart_command=tui_restart_command(chat_thread_id),
        )
        AuditLog().append(
            "control_console_bridge_restart_requested",
            thread_id=chat_thread_id,
            pane_id=result.get("pane_id"),
            status=result.get("status"),
        )
        return result

    def _console_restart_request_details(self) -> dict:
        return console_restart_request_details(
            public_url=self.config.public_url,
            chat_thread_id=getattr(self.server, "omnidoer_chat_thread_id", None),
            detached_thread_resume_allowed=bool(getattr(self.server, "omnidoer_chat_allow_detached_thread_resume", False)),
        )

    def _create_console_restart_request(self, store: RequestStore, session: ControlSession | None, *, details: dict | None = None) -> tuple[object, bool]:
        return create_or_renew_console_restart_request(
            store,
            public_url=self.config.public_url,
            details=dict(details or self._console_restart_request_details()),
            session=session,
            requires_pairing=self._requires_pairing(),
        )

    def _set_session_cookie(self, session_id: str, token: str) -> None:
        secure = "; Secure" if self.config.mode == "cloud_direct" else ""
        self.send_header(
            "set-cookie",
            f"omnidoer_session={session_id}:{token}; HttpOnly; SameSite=Strict{secure}; Path=/; Max-Age={CONTROL_SESSION_TTL_SECONDS}",
        )

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

    def _send_pairing_error(self, exc: Exception) -> None:
        reason = str(exc).strip() or type(exc).__name__
        status = HTTPStatus.UNAUTHORIZED
        code = "pairing_failed"
        if isinstance(exc, ValueError):
            lower = reason.lower()
            if "expired" in lower:
                status = HTTPStatus.GONE
                code = "pairing_code_expired"
            elif "already used" in lower:
                status = HTTPStatus.CONFLICT
                code = "pairing_code_used"
            elif "invalid" in lower:
                code = "pairing_code_invalid"
        self._send_json(status, {"error": code, "reason": reason})

    def do_GET(self) -> None:
        if self._plain_http_on_direct_tls_port():
            self._send_https_required()
            return
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        parts = path.strip("/").split("/")
        store = RequestStore()
        if path in {"/pair", "/pair/"}:
            self._send_pwa_index()
            return
        if path == "/api/status":
            config = getattr(self.server, "omnidoer_config", None)
            chat_thread_id = getattr(self.server, "omnidoer_chat_thread_id", None)
            detached_runner_allowed = bool(getattr(self.server, "omnidoer_chat_allow_detached_thread_resume", False))
            from omnidoer.omni_control.chat_runner import (
                active_tui_process_bridge_status,
                active_mcp_sidecar_status,
                browser_takeover_readiness,
                control_chat_sync_diagnostics,
                live_tui_bridge_active,
                live_tui_session_active,
                native_console_bridge_install_status,
                tui_bridge_heartbeat_status,
                tui_restart_command,
            )
            from omnidoer.omni_control.tui_legacy_relay import legacy_tui_relay_status

            bridge_heartbeat = tui_bridge_heartbeat_status(chat_thread_id)
            tui_bridge_active = live_tui_bridge_active(chat_thread_id)
            tui_session_active = live_tui_session_active(chat_thread_id)
            waiting_for_tui_bridge = bool(chat_thread_id and not tui_bridge_active)
            legacy_relay = legacy_tui_relay_status(chat_thread_id) if waiting_for_tui_bridge else {"active": False}
            install_status = native_console_bridge_install_status()
            active_process_bridge = active_tui_process_bridge_status(chat_thread_id)
            mcp_sidecar = active_mcp_sidecar_status(chat_thread_id)
            mcp_sidecar_restart_required = bool(mcp_sidecar.get("restart_required"))
            heartbeat_age = bridge_heartbeat.get("age_seconds")
            quota_summary = _active_terminal_quota_summary(chat_thread_id) or _recent_chat_quota_summary() or {}
            quota_refresh = self._maybe_queue_quota_status_refresh(
                chat_thread_id=chat_thread_id,
                tui_bridge_active=tui_bridge_active,
                quota_summary=quota_summary,
            )
            sync_diagnostics = control_chat_sync_diagnostics(
                thread_id=chat_thread_id,
                tui_bridge_active=tui_bridge_active,
                tui_session_active=tui_session_active,
                install_status=install_status,
                legacy_relay=legacy_relay,
                active_process_bridge=active_process_bridge,
                mcp_sidecar=mcp_sidecar,
                bridge_heartbeat_age_seconds=heartbeat_age,
                bridge_heartbeat=bridge_heartbeat,
                detached_thread_resume_allowed=detached_runner_allowed,
            )
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "mode": getattr(config, "mode", "local_dev"),
                    "public_url": getattr(config, "public_url", "http://127.0.0.1:8787"),
                    "agent_llm_receives_secrets": False,
                    "quota": quota_summary,
                    "quota_refresh": quota_refresh,
                    "chat_runner": {
                        "thread_id": chat_thread_id,
                        "tui_bridge_active": tui_bridge_active,
                        "tui_session_active": tui_session_active,
                        "waiting_for_tui_bridge": waiting_for_tui_bridge,
                        "restart_required": waiting_for_tui_bridge or mcp_sidecar_restart_required,
                        "restart_command": tui_restart_command(chat_thread_id) if waiting_for_tui_bridge or mcp_sidecar_restart_required else None,
                        "native_console_bridge": install_status,
                        "active_tui_process_bridge": active_process_bridge,
                        "mcp_sidecar": mcp_sidecar,
                        "bridge_heartbeat": bridge_heartbeat,
                        "bridge_heartbeat_age_seconds": heartbeat_age,
                        "legacy_tui_relay": legacy_relay,
                        "detached_thread_resume_allowed": detached_runner_allowed,
                        "sync_diagnostics": sync_diagnostics,
                        "browser_takeover": browser_takeover_readiness(
                            diagnostics=sync_diagnostics,
                            mcp_sidecar=mcp_sidecar,
                        ),
                    },
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
        if path == "/api/auth/check":
            try:
                session = self._require_access()
            except PermissionError:
                self._send_json(
                    HTTPStatus.UNAUTHORIZED,
                    {
                        "authenticated": False,
                        "error": "unauthorized",
                        "secret_fields_allowed": False,
                    },
                )
                return
            self._send_json(
                HTTPStatus.OK,
                {
                    "authenticated": True,
                    "session": session.to_public_dict() if session else None,
                    "device_id": session.device_id if session else None,
                    "secret_fields_allowed": False,
                },
            )
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
                    snapshots = int(query.get("snapshots", [str(REQUEST_STREAM_DEFAULT_SNAPSHOTS)])[0])
                    interval = float(query.get("interval", ["2"])[0])
                    self._send_sse_stream(store, session, snapshots=snapshots, interval=interval)
                else:
                    self._send_sse(self._sse_payload(store, session))
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid stream options"})
            return
        if path in {"/api/chat/messages", "/api/chat/records"}:
            try:
                self._require_access()
                query = parse_qs(parsed_url.query)
                limit = int(query.get("limit", ["200"])[0])
                after = query.get("after_sequence", [None])[0]
                session_id = self._chat_session_id_from_query(query)
                compact = query.get("compact", ["0"])[0] == "1"
                self._send_json(
                    HTTPStatus.OK,
                    self._chat_payload(
                        limit=limit,
                        after_sequence=int(after) if after else None,
                        session_id=session_id,
                        compact=compact,
                    ),
                )
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid chat options"})
            return
        if path == "/api/chat/sessions":
            try:
                self._require_access()
                self._send_json(HTTPStatus.OK, ChatSessionStore().list())
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        if path == "/api/chat/events":
            try:
                self._require_access()
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(CHAT_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["1"])[0])
                limit = int(query.get("limit", ["200"])[0])
                after = query.get("after_sequence", [None])[0]
                session_id = self._chat_session_id_from_query(query)
                compact = query.get("compact", ["0"])[0] == "1"
                if query.get("stream", ["0"])[0] == "1":
                    self._send_chat_sse_stream(
                        snapshots=snapshots,
                        interval=interval,
                        limit=limit,
                        after_sequence=int(after) if after else None,
                        session_id=session_id,
                        compact=compact,
                    )
                else:
                    self._send_sse(
                        self._chat_payload(
                            limit=limit,
                            after_sequence=int(after) if after else None,
                            session_id=session_id,
                            compact=compact,
                        ),
                        event="chat",
                    )
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid chat stream options"})
            return
        if path == "/api/browser/contexts/events":
            try:
                self._require_access()
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(BROWSER_CONTEXT_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["1"])[0])
                if query.get("stream", ["0"])[0] == "1":
                    self._send_browser_context_sse_stream(snapshots=snapshots, interval=interval)
                else:
                    self._send_sse(self._browser_context_payload(), event="browser_contexts")
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid browser context stream options"})
            return
        if path == "/api/ws/chat":
            try:
                from omnidoer.omni_control.websocket import websocket_origin_allowed

                if self._requires_pairing() and not websocket_origin_allowed(self.headers.get("origin"), self.config.public_origin):
                    raise PermissionError("websocket origin rejected")
                if (self.headers.get("upgrade") or "").lower() != "websocket":
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "websocket upgrade required"})
                    return
                self._require_access()
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(CHAT_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["1"])[0])
                limit = int(query.get("limit", ["200"])[0])
                after = query.get("after_sequence", [None])[0]
                session_id = self._chat_session_id_from_query(query)
                compact = query.get("compact", ["0"])[0] == "1"
                self._send_chat_websocket_stream(
                    snapshots=snapshots,
                    interval=interval,
                    limit=limit,
                    after_sequence=int(after) if after else None,
                    session_id=session_id,
                    compact=compact,
                )
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid chat websocket options"})
            return
        if path == "/api/ws/browser/contexts":
            try:
                from omnidoer.omni_control.websocket import websocket_origin_allowed

                if self._requires_pairing() and not websocket_origin_allowed(self.headers.get("origin"), self.config.public_origin):
                    raise PermissionError("websocket origin rejected")
                if (self.headers.get("upgrade") or "").lower() != "websocket":
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "websocket upgrade required"})
                    return
                self._require_access()
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(BROWSER_CONTEXT_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["1"])[0])
                self._send_browser_context_websocket_stream(snapshots=snapshots, interval=interval)
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid browser context websocket options"})
            return
        if path.startswith("/api/ws/requests/") and path.endswith("/frames"):
            try:
                from omnidoer.omni_control.websocket import websocket_origin_allowed

                if self._requires_pairing() and not websocket_origin_allowed(self.headers.get("origin"), self.config.public_origin):
                    raise PermissionError("websocket origin rejected")
                if (self.headers.get("upgrade") or "").lower() != "websocket":
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "websocket upgrade required"})
                    return
                session = self._require_access()
                parts = path.strip("/").split("/")
                if len(parts) != 5 or parts[:3] != ["api", "ws", "requests"] or parts[4] != "frames":
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown websocket stream"})
                    return
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(BROWSER_FRAME_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["0.75"])[0])
                frame_profile = normalize_frame_profile(query.get("profile", [None])[0])
                self._send_takeover_frame_websocket_stream(
                    store,
                    session,
                    parts[3],
                    snapshots=snapshots,
                    interval=interval,
                    frame_profile=frame_profile,
                )
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "request not found"})
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid frame websocket options"})
            return
        if path.startswith("/api/ws/browser/contexts/") and path.endswith("/frames"):
            try:
                from omnidoer.omni_control.websocket import websocket_origin_allowed

                if self._requires_pairing() and not websocket_origin_allowed(self.headers.get("origin"), self.config.public_origin):
                    raise PermissionError("websocket origin rejected")
                if (self.headers.get("upgrade") or "").lower() != "websocket":
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "websocket upgrade required"})
                    return
                self._require_access()
                parts = path.strip("/").split("/")
                if len(parts) != 6 or parts[:4] != ["api", "ws", "browser", "contexts"] or parts[5] != "frames":
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown websocket stream"})
                    return
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(BROWSER_FRAME_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["0.75"])[0])
                frame_profile = normalize_frame_profile(query.get("profile", [None])[0])
                self._send_browser_context_frame_websocket_stream(
                    unquote(parts[4]),
                    snapshots=snapshots,
                    interval=interval,
                    frame_profile=frame_profile,
                )
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid browser frame websocket options"})
            return
        if path == "/api/ws/requests":
            try:
                from omnidoer.omni_control.websocket import websocket_origin_allowed

                if self._requires_pairing() and not websocket_origin_allowed(self.headers.get("origin"), self.config.public_origin):
                    raise PermissionError("websocket origin rejected")
                if (self.headers.get("upgrade") or "").lower() != "websocket":
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "websocket upgrade required"})
                    return
                session = self._require_access()
                query = parse_qs(parsed_url.query)
                snapshots = int(query.get("snapshots", [str(REQUEST_STREAM_DEFAULT_SNAPSHOTS)])[0])
                interval = float(query.get("interval", ["2"])[0])
                self._send_websocket_stream(store, session, snapshots=snapshots, interval=interval)
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            except CLIENT_DISCONNECT_EXCEPTIONS:
                pass
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid websocket options"})
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
        if path == "/api/browser/contexts":
            try:
                self._require_access()
                from omnidoer.omni_takeover.cross_process import list_contexts

                self._send_json(HTTPStatus.OK, {"contexts": list_contexts(), "secret_exposed_to_model": False})
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        if len(parts) == 5 and parts[:3] == ["api", "browser", "contexts"] and parts[4] == "frame":
            try:
                self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            try:
                from omnidoer.omni_takeover.cross_process import read_frame

                context_id = unquote(parts[3])
                query = parse_qs(parsed_url.query)
                frame_profile = normalize_frame_profile(query.get("profile", [None])[0])
                browser = get_browser_context(context_id)
                if browser is not None:
                    frame = browser.takeover_frame(frame_profile=frame_profile)
                else:
                    frame = read_frame(context_id)
                if frame is None:
                    self._send_json(HTTPStatus.CONFLICT, {"error": "browser_frame_unavailable", "secret_exposed_to_model": False})
                    return
                self._send_json(HTTPStatus.OK, {**frame, "preview_only": True, "secret_exposed_to_model": False})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 6 and parts[:3] == ["api", "browser", "contexts"] and parts[4] == "input-results":
            try:
                session = self._require_access()
            except PermissionError:
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            try:
                from omnidoer.omni_takeover.cross_process import read_input_event_result, wait_for_input_event_result

                context_id = unquote(parts[3])
                event_id = unquote(parts[5])
                query = parse_qs(parsed_url.query)
                wait_seconds = min(
                    TAKEOVER_INPUT_RESULT_WAIT_MAX_SECONDS,
                    max(0.0, float(query.get("wait", ["0"])[0] or 0.0)),
                )
                preview = read_input_event_result(context_id, event_id, consume=False)
                if preview is None and wait_seconds > 0:
                    preview = wait_for_input_event_result(
                        context_id,
                        event_id,
                        timeout_seconds=wait_seconds,
                        consume=False,
                    )
                if preview is None:
                    self._send_json(HTTPStatus.ACCEPTED, {"status": "pending", "secret_exposed_to_model": False})
                    return
                request = self._get_request_for_session(store, str(preview.get("request_id") or ""), session)
                if request.browser_context_id != context_id:
                    self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                    return
                result = read_input_event_result(context_id, event_id, consume=True)
                if result is None:
                    self._send_json(HTTPStatus.ACCEPTED, {"status": "pending", "secret_exposed_to_model": False})
                    return
                self._send_json(HTTPStatus.OK, result)
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "request not found"})
            except PermissionError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
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
                    query = parse_qs(parsed_url.query)
                    frame_profile = normalize_frame_profile(query.get("profile", [None])[0])
                    request = self._get_request_for_session(store, request_id, session)
                    frame = self._takeover_request_frame(request_id, request, frame_profile=frame_profile)
                    if frame is None:
                        self._send_json(HTTPStatus.CONFLICT, {"error": "browser_frame_unavailable", "secret_exposed_to_model": False})
                        return
                    store.record_takeover_frame(request_id, frame)
                    self._send_json(HTTPStatus.OK, frame)
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
        if self._plain_http_on_direct_tls_port():
            self._send_https_required()
            return
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
                AuditLog().append(
                    "control_device_paired",
                    device_id=result.device.device_id,
                    device_fingerprint=result.device.fingerprint,
                    status="ok",
                )
                PAIR_RATE_LIMIT.clear(remote_key)
            except Exception as exc:
                PAIR_RATE_LIMIT.record_failure(remote_key)
                AuditLog().append("control_pairing_failed", status=type(exc).__name__, reason=str(exc).strip())
                self._send_pairing_error(exc)
            return
        if path == "/api/console/restart-bridge":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                if body.get("confirm_restart") is not True:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": "confirm_restart_required"})
                    return
                self._send_json(HTTPStatus.OK, self._restart_console_bridge())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/console/restart-bridge/request":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                request, reused = self._create_console_restart_request(store, session)
                self._send_json(
                    HTTPStatus.OK if reused else HTTPStatus.CREATED,
                    {
                        "status": "approval_request_reused" if reused else "approval_request_created",
                        "request": request.to_public_dict(),
                        "reused": reused,
                        "secret_exposed_to_model": False,
                    },
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
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
        if path == "/api/chat/messages":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                text = str(body.get("text") or "")
                client_message_id = str(body.get("client_message_id") or "") or None
                chat_session_id = validate_chat_session_id(body.get("session_id") or ChatSessionStore().active_session_id())
                local_cli_response = self._handle_control_cli_command(
                    text=text,
                    client_message_id=client_message_id,
                    session=session,
                )
                if local_cli_response is not None:
                    self._send_json(HTTPStatus.CREATED, local_cli_response)
                    return
                upload_store = ChatUploadStore()
                upload_store.cleanup_expired(ttl_seconds=self._chat_upload_ttl_seconds())
                chat_store = ChatStore(session_id=chat_session_id)
                message = chat_store.append(
                    role="user",
                    text=text,
                    source="control_client",
                    author_device_id=session.device_id if session else None,
                    client_message_id=client_message_id,
                    reply_to_message_id=str(body.get("reply_to_message_id") or "") or None,
                    attachments=validate_uploaded_attachments(body.get("attachments"), upload_store.directory),
                )
                delivery = (
                    self._try_deliver_chat_to_live_console(message.message_id)
                    if chat_session_id == DEFAULT_CHAT_SESSION_ID
                    else {"attempted": False, "reason": "background_session", "secret_exposed_to_model": False}
                )
                try:
                    payload = chat_store.get(message.message_id).to_public_dict()
                except KeyError:
                    payload = message.to_public_dict()
                payload["live_console_delivery"] = delivery
                self._send_json(HTTPStatus.CREATED, payload)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/sessions":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                created = ChatSessionStore().create(title=str(body.get("title") or "") or None)
                self._send_json(
                    HTTPStatus.CREATED,
                    {"session": created.to_public_dict(), **ChatSessionStore().list()},
                )
            except ValueError as exc:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 5 and parts[:3] == ["api", "chat", "sessions"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            session_id, action = parts[3], parts[4]
            try:
                if action == "activate":
                    activated = ChatSessionStore().activate(session_id)
                    self._send_json(HTTPStatus.OK, {"session": activated.to_public_dict(), **ChatSessionStore().list()})
                    return
                if action == "close":
                    closed = ChatSessionStore().close(session_id)
                    self._send_json(HTTPStatus.OK, {**closed, **ChatSessionStore().list()})
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "chat session not found"})
            except ValueError as exc:
                self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/session/new":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                archived = ChatStore().archive_and_reset()
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "status": "created",
                        "session_started_at": time.time(),
                        "archived": archived,
                        "secret_fields_allowed": False,
                        "control_client_calls_model": False,
                    },
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/attachments":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                ttl_seconds = self._chat_upload_ttl_seconds()
                upload_store = ChatUploadStore()
                upload_store.cleanup_expired(ttl_seconds=ttl_seconds)
                uploads = [
                    upload_store.save(
                        filename=file["filename"],
                        content=file["content"],
                        content_type=file["content_type"],
                        ttl_seconds=ttl_seconds,
                    ).to_public_dict()
                    for file in self._read_multipart_files()
                ]
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "attachments": uploads,
                        "directory": str(upload_store.directory),
                        "ttl_seconds": ttl_seconds,
                        "secret_fields_allowed": False,
                    },
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path.startswith("/api/browser/contexts/") and path.endswith("/takeover"):
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                from omnidoer.omni_takeover.cross_process import get_context
                from omnidoer.omni_takeover.relay import request_user_control

                context_id = unquote(path.strip("/").split("/")[3])
                context = get_context(context_id)
                if not context:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "browser_context_not_found"})
                    return
                body = self._read_json()
                reason = str(body.get("reason") or "User requested browser takeover from Control Client")
                for existing in store.list():
                    if (
                        existing.browser_context_id == context_id
                        and existing.request_type in {"human_takeover", "account_registration"}
                        and existing.status == "user_control"
                    ):
                        if not self._request_allowed_for_session(existing, session):
                            self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                            return
                        self._send_json(HTTPStatus.OK, {**existing.to_public_dict(), "reused": True})
                        return
                request = request_user_control(
                    origin=str(context.get("origin") or ""),
                    top_level_url=str(context.get("current_url") or context.get("origin") or ""),
                    reason=reason,
                    browser_context_id=context_id,
                    risk_level=str(body.get("risk_level") or "high"),
                    allowed_device_id=session.device_id if session else None,
                )
                payload = {**request.to_public_dict(), "reused": False}
                if body.get("notify_agent", True) is not False:
                    payload["agent_pause"] = self._safe_queue_agent_instruction(
                        text=reason,
                        client_message_id=str(body.get("client_message_id") or f"control_pause_{int(time.time() * 1000)}"),
                        session=session,
                    )
                self._send_json(HTTPStatus.CREATED, payload)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/messages/next":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                message = ChatStore().next_user_message(claim=bool(body.get("claim", True)))
                if message is None:
                    self._send_json(HTTPStatus.OK, {"status": "empty", "secret_fields_allowed": False})
                    return
                self._send_json(HTTPStatus.OK, {"status": "ok", "message": message.to_public_dict()})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/messages/assistant":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                message = ChatStore().append(
                    role="assistant",
                    text=str(body.get("text") or ""),
                    status=str(body.get("status") or "completed"),
                    source=str(body.get("source") or "agent"),
                    reply_to_message_id=str(body.get("reply_to_message_id") or "") or None,
                )
                self._send_json(HTTPStatus.CREATED, message.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if path == "/api/chat/records":
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            try:
                body = self._read_json()
                record = ChatStore().append_record(
                    record_type=str(body.get("record_type") or "note"),
                    text=str(body.get("text") or ""),
                    role=str(body.get("role") or "") or None,
                    message_id=str(body.get("message_id") or "") or None,
                    source=str(body.get("source") or "agent"),
                    data=body.get("data") if isinstance(body.get("data"), dict) else None,
                )
                self._send_json(HTTPStatus.CREATED, record.to_public_dict())
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        if len(parts) == 5 and parts[:3] == ["api", "chat", "messages"]:
            try:
                session = self._require_access(mutating=True)
                self._check_mutation_rate_limit(session)
            except PermissionError as exc:
                self._send_permission_error(exc)
                return
            message_id, action = parts[3], parts[4]
            try:
                body = self._read_json()
                if action == "delta":
                    message = ChatStore().append_delta(message_id, str(body.get("delta") or ""))
                elif action == "complete":
                    text = body.get("text")
                    message = ChatStore().complete(message_id, text=str(text) if text is not None else None)
                elif action == "cancel":
                    message = ChatStore().cancel(message_id)
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                    return
                self._send_json(HTTPStatus.OK, message.to_public_dict())
            except KeyError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "message not found"})
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
                AuditLog().append(
                    "control_device_revoked",
                    device_id=device.device_id,
                    revoked_sessions=len(revoked_sessions),
                    status="revoked",
                )
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
                AuditLog().append(
                    "control_session_revoked",
                    session_id=revoked.session_id,
                    device_id=revoked.device_id,
                    status="revoked",
                )
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
                console_restart_result = None
                agent_continue_result = None
                if action == "approve":
                    body = self._read_json()
                    if control_request.request_type in {"payment_approval", "console_restart"} and (
                        body.get("explicit_user_confirmation") is not True or body.get("request_id") != request_id
                    ):
                        self._send_json(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": "explicit_user_confirmation_required",
                                "secret_exposed_to_model": False,
                            },
                        )
                        return
                    request = store.approve(request_id)
                    if control_request.request_type == "console_restart":
                        console_restart_result = self._restart_console_bridge()
                        request = store.consume_approval(request_id)
                elif action == "deny":
                    request = store.deny(request_id)
                elif action == "release":
                    request = store.release_takeover(request_id)
                    if control_request.request_type in {"human_takeover", "account_registration"}:
                        agent_continue_result = self._safe_queue_agent_instruction(
                            text="I have finished controlling the browser. Continue from the current page state and resume the task.",
                            client_message_id=f"control_continue_{int(time.time() * 1000)}",
                            session=session,
                        )
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
                    body = self._read_json()
                    event = event_from_dict(body)
                    try:
                        store.validate_takeover_input(request_id, event)
                    except ValueError as exc:
                        if str(exc) == "stale takeover frame":
                            self._send_json(
                                HTTPStatus.CONFLICT,
                                {
                                    "error": "stale_takeover_frame",
                                    "secret_exposed_to_model": False,
                                },
                            )
                            return
                        if str(exc) == "takeover coordinates out of frame bounds":
                            self._send_json(
                                HTTPStatus.BAD_REQUEST,
                                {
                                    "error": "takeover_coordinates_out_of_bounds",
                                    "secret_exposed_to_model": False,
                                },
                            )
                            return
                        raise
                    if browser is None:
                        from omnidoer.omni_takeover.cross_process import enqueue_input_event, get_context, wait_for_input_event_result

                        if get_context(request.browser_context_id or ""):
                            queued = enqueue_input_event(request.browser_context_id or "", request_id, body)
                            result = wait_for_input_event_result(
                                request.browser_context_id or "",
                                str(queued.get("event_id") or ""),
                            )
                            if result is not None:
                                status = HTTPStatus.CONFLICT if result.get("status") == "event_failed" else HTTPStatus.OK
                                self._send_json(status, result)
                                return
                            self._send_json(HTTPStatus.ACCEPTED, queued)
                            return
                        self._send_json(HTTPStatus.CONFLICT, {"error": "browser context is not connected"})
                        return
                    self._send_json(HTTPStatus.OK, apply_input_event(request_id, event, browser_controller=browser))
                    return
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
                    return
                payload = request.to_public_dict()
                if console_restart_result is not None:
                    payload["console_restart"] = console_restart_result
                if agent_continue_result is not None:
                    payload["agent_continue"] = agent_continue_result
                self._send_json(HTTPStatus.OK, payload)
            except PermissionError:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": type(exc).__name__})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_HEAD(self) -> None:
        if self._plain_http_on_direct_tls_port():
            self._send_https_required(include_body=False)
            return
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
    chat_runner: bool = False,
    chat_runner_interval: float = 1.0,
    chat_runner_cwd: str | None = None,
    chat_codex_bin: str | None = None,
    chat_thread_id: str | None = None,
    chat_codex_args: list[str] | None = None,
    chat_upload_ttl: str | int | None = None,
    chat_allow_detached_thread_resume: bool = False,
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
    tls_context = None
    if tls_cert and tls_key:
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls_context.load_cert_chain(tls_cert, tls_key)
    elif tls_self_signed_dev:
        tls_context = _self_signed_context(host)
    server = TLSAwareThreadingHTTPServer((host, port), ControlHandler, tls_context=tls_context)
    server.omnidoer_config = config  # type: ignore[attr-defined]
    server.omnidoer_direct_tls = tls_context is not None  # type: ignore[attr-defined]
    server.omnidoer_chat_thread_id = chat_thread_id  # type: ignore[attr-defined]
    server.omnidoer_chat_allow_detached_thread_resume = chat_allow_detached_thread_resume  # type: ignore[attr-defined]
    upload_ttl_seconds = chat_upload_ttl_seconds(chat_upload_ttl)
    server.omnidoer_chat_upload_ttl_seconds = upload_ttl_seconds  # type: ignore[attr-defined]
    ChatUploadStore().cleanup_expired(ttl_seconds=upload_ttl_seconds)
    cleanup_interval = max(60, min(upload_ttl_seconds, 3600))

    def cleanup_chat_uploads() -> None:
        while True:
            time.sleep(cleanup_interval)
            ChatUploadStore().cleanup_expired(ttl_seconds=upload_ttl_seconds)

    threading.Thread(target=cleanup_chat_uploads, name="omnidoer-chat-upload-cleanup", daemon=True).start()
    record_control_service_runtime(config)
    if chat_thread_id:
        start_current_session_sync_request_maintainer(
            config=config,
            chat_thread_id=chat_thread_id,
            detached_thread_resume_allowed=bool(chat_allow_detached_thread_resume),
        )
    if tls_self_signed_dev:
        print("WARNING: --tls-self-signed-dev is for localhost/test only. Use a real certificate or reverse proxy for Cloud Direct.")
    if insecure_dev_public:
        print("WARNING: --insecure-dev-public disables Cloud Direct HTTPS enforcement. Use only for temporary testing.")
    if chat_runner:
        from omnidoer.omni_control.chat_runner import start_chat_session_runner_supervisor
        from omnidoer.omni_control.tui_legacy_relay import start_legacy_tui_relay_thread

        detached_runner_allowed = bool(chat_allow_detached_thread_resume or not chat_thread_id)
        if detached_runner_allowed:
            start_chat_session_runner_supervisor(
                codex_bin=chat_codex_bin,
                cwd=chat_runner_cwd,
                thread_id=chat_thread_id,
                extra_args=chat_codex_args or [],
                poll_interval=chat_runner_interval,
                require_live_tui_for_thread=bool(chat_thread_id),
                allow_detached_thread_resume=bool(chat_allow_detached_thread_resume),
            )
        if chat_thread_id:
            start_legacy_tui_relay_thread(thread_id=chat_thread_id, poll_interval=chat_runner_interval)
        if chat_thread_id and detached_runner_allowed:
            print(f"OmniDoer chat runner enabled: Control Client messages resume Codex thread {chat_thread_id}.")
        elif chat_thread_id:
            print(
                "OmniDoer chat runner bound to live console only: Control Client messages use native bridge or terminal relay, not detached codex exec."
            )
        else:
            print("OmniDoer chat runner enabled: Control Client messages stream through codex exec --json.")
    print(f"OmniDoer Control Service listening on {config.public_url} mode={config.mode}")
    server.serve_forever()

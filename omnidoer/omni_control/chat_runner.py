"""Bridge queued Control Client chat messages to Codex JSON events."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from omnidoer.omni_control.chat import ChatMessage, ChatStore
from omnidoer.omni_control.chat_uploads import image_attachment_paths
from omnidoer.paths import state_file


DEFAULT_RECORD_TEXT_LIMIT = 6000
TUI_BRIDGE_HEARTBEAT_NAME = "control_chat_bridge_heartbeat"
TUI_BRIDGE_STALE_SECONDS = 5.0
TUI_BRIDGE_INSTALL_MARKERS = (
    b"control_chat_bridge_heartbeat",
    b"chat-log-user",
    b"failed to publish OmniDoer user chat message",
)
_bridge_install_cache: dict[tuple[str, int, int], dict[str, Any]] = {}


def find_codex_binary(explicit: str | None = None) -> str | None:
    candidates = [
        explicit,
        os.environ.get("OMNIDOER_CHAT_CODEX_BIN"),
        os.environ.get("OMNIDOER_CODEX_BIN"),
        os.environ.get("OMNIDOER_REAL_CODEX"),
        "/usr/local/lib/omnidoer/codex",
        shutil.which("codex"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _clip(text: str, limit: int = DEFAULT_RECORD_TEXT_LIMIT) -> str:
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n...[truncated {omitted} chars]"


def _status(value: str | None) -> str:
    return value or "unknown"


def live_tui_bridge_active(*, now: float | None = None) -> bool:
    path = state_file(TUI_BRIDGE_HEARTBEAT_NAME)
    try:
        age = (now or time.time()) - path.stat().st_mtime
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return age <= TUI_BRIDGE_STALE_SECONDS


def tui_bridge_heartbeat_age_seconds(*, now: float | None = None) -> float | None:
    path = state_file(TUI_BRIDGE_HEARTBEAT_NAME)
    try:
        return max(0.0, (now or time.time()) - path.stat().st_mtime)
    except (FileNotFoundError, OSError):
        return None


def tui_restart_command(thread_id: str | None) -> str | None:
    if not thread_id:
        return None
    return f"omnidoer console resume {thread_id}"


def _missing_binary_markers(path: Path, markers: tuple[bytes, ...]) -> list[str]:
    remaining = set(markers)
    overlap = max(len(marker) for marker in markers) - 1
    tail = b""
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            window = tail + chunk
            for marker in list(remaining):
                if marker in window:
                    remaining.remove(marker)
            tail = window[-overlap:] if overlap else b""
    return [marker.decode("utf-8", "replace") for marker in markers if marker in remaining]


def native_console_bridge_install_status(codex_bin: str | None = None) -> dict[str, Any]:
    binary = find_codex_binary(codex_bin)
    if not binary:
        return {"ready": False, "reason": "codex_binary_not_found"}
    path = Path(binary)
    try:
        stat = path.stat()
    except OSError:
        return {"ready": False, "reason": "codex_binary_unreadable", "codex_binary": str(path)}
    cache_key = (str(path), stat.st_mtime_ns, stat.st_size)
    cached = _bridge_install_cache.get(cache_key)
    if cached is not None:
        return dict(cached)
    try:
        missing = _missing_binary_markers(path, TUI_BRIDGE_INSTALL_MARKERS)
    except OSError:
        return {"ready": False, "reason": "codex_binary_unreadable", "codex_binary": str(path)}
    status = {
        "ready": not missing,
        "reason": "ready" if not missing else "missing_bridge_markers",
        "codex_binary": str(path),
        "marker_count": len(TUI_BRIDGE_INSTALL_MARKERS),
        "missing_markers": missing,
    }
    _bridge_install_cache.clear()
    _bridge_install_cache[cache_key] = dict(status)
    return status


def control_chat_sync_diagnostics(
    *,
    thread_id: str | None,
    tui_bridge_active: bool,
    tui_session_active: bool,
    install_status: dict[str, Any],
    legacy_relay: dict[str, Any],
    bridge_heartbeat_age_seconds: float | None = None,
    detached_thread_resume_allowed: bool = False,
) -> dict[str, Any]:
    native_ready = bool(install_status.get("ready"))
    legacy_active = bool(legacy_relay.get("active"))
    bound_thread = bool(thread_id)
    if tui_bridge_active:
        state = "native_bridge_active"
    elif legacy_active:
        state = "legacy_terminal_relay"
    elif bound_thread and tui_session_active:
        state = "current_cli_waiting_for_bridge"
    elif bound_thread:
        state = "bound_thread_without_live_cli"
    else:
        state = "background_runner"
    requires_restart = state in {"legacy_terminal_relay", "current_cli_waiting_for_bridge", "bound_thread_without_live_cli"}
    return {
        "state": state,
        "thread_bound": bound_thread,
        "native_bridge_installed": native_ready,
        "current_cli_process_active": bool(tui_session_active),
        "current_cli_context_attached": bool(tui_bridge_active),
        "current_cli_reachable": bool(tui_bridge_active or legacy_active),
        "phone_to_current_cli_delivery": "structured_bridge" if tui_bridge_active else "terminal_relay" if legacy_active else "not_connected",
        "current_cli_to_phone_stream": "structured_records" if tui_bridge_active else "terminal_snapshot" if legacy_active else "not_connected",
        "structured_streaming": bool(tui_bridge_active),
        "temporary_terminal_relay": legacy_active,
        "requires_restart_for_native_sync": requires_restart,
        "restart_ready": bool(requires_restart and native_ready and bound_thread),
        "detached_thread_resume_allowed": bool(detached_thread_resume_allowed),
        "bridge_heartbeat_age_seconds": bridge_heartbeat_age_seconds,
    }


def _cmdline_is_interactive_tui_for_thread(cmdline: list[str], thread_id: str) -> bool:
    if not cmdline or not thread_id:
        return False
    args = cmdline[1:]
    if "exec" in args:
        return False
    return "resume" in args and thread_id in args


def live_tui_session_active(thread_id: str | None, *, proc_root: Path | str = "/proc") -> bool:
    if not thread_id:
        return False
    root = Path(proc_root)
    try:
        entries = list(root.iterdir())
    except OSError:
        return False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        cmdline = [part.decode("utf-8", "ignore") for part in raw.split(b"\0") if part]
        if _cmdline_is_interactive_tui_for_thread(cmdline, thread_id):
            return True
    return False


class CodexJsonEventBridge:
    def __init__(self, store: ChatStore, assistant: ChatMessage):
        self.store = store
        self.assistant = assistant
        self.item_text_by_id: dict[str, str] = {}

    def record(self, record_type: str, text: str, *, role: str | None = None, data: dict[str, Any] | None = None) -> None:
        self.store.append_record(
            record_type=record_type,
            text=_clip(text),
            role=role,
            message_id=self.assistant.message_id,
            source="codex_exec_json",
            data=data or {},
        )

    def handle(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        if event_type == "thread.started":
            self.record("status", f"Codex thread started: {event.get('thread_id')}", role="system", data={"event": event_type})
            return
        if event_type == "turn.started":
            self.record("status", "Codex turn started.", role="system", data={"event": event_type})
            return
        if event_type == "turn.completed":
            usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
            self.record("status", f"Codex turn completed. usage={_json_text(usage)}", role="system", data={"event": event_type})
            return
        if event_type == "turn.failed":
            error = event.get("error") if isinstance(event.get("error"), dict) else {}
            self.record("error", f"Codex turn failed: {_json_text(error)}", role="system", data={"event": event_type})
            return
        if event_type == "error":
            self.record("error", str(event.get("message") or _json_text(event)), role="system", data={"event": event_type})
            return
        if event_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            if isinstance(item, dict):
                self._handle_item(item, event_type)
            return
        self.record("note", _json_text(event), role="system", data={"event": event_type or "unknown"})

    def _handle_item(self, item: dict[str, Any], event_type: str) -> None:
        item_type = str(item.get("type") or "")
        item_id = str(item.get("id") or "")
        if item_type == "agent_message":
            self._handle_agent_message(item, item_id)
            return
        if item_type == "reasoning":
            text = str(item.get("text") or "")
            if text:
                self.record("note", f"Reasoning summary:\n{text}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "command_execution":
            self._handle_command_execution(item, event_type, item_id)
            return
        if item_type == "mcp_tool_call":
            self._handle_mcp_tool_call(item, event_type, item_id)
            return
        if item_type == "file_change":
            self.record("note", f"File changes: {_json_text(item.get('changes') or [])}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "web_search":
            self.record("tool_call", f"Web search: {_json_text(item)}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "todo_list":
            self.record("status", f"Plan update: {_json_text(item.get('items') or [])}", role="assistant", data={"event": event_type, "item_id": item_id})
            return
        if item_type == "error":
            self.record("error", str(item.get("message") or _json_text(item)), role="system", data={"event": event_type, "item_id": item_id})
            return
        self.record("note", _json_text(item), role="system", data={"event": event_type, "item_id": item_id, "item_type": item_type})

    def _handle_agent_message(self, item: dict[str, Any], item_id: str) -> None:
        text = str(item.get("text") or "")
        previous = self.item_text_by_id.get(item_id, "")
        if not text or text == previous:
            return
        if text.startswith(previous):
            delta = text[len(previous) :]
        else:
            delta = text
        self.item_text_by_id[item_id] = text
        self.assistant = self.store.append_delta(self.assistant.message_id, delta)

    def _handle_command_execution(self, item: dict[str, Any], event_type: str, item_id: str) -> None:
        command = str(item.get("command") or "")
        status = _status(item.get("status"))
        if event_type == "item.started":
            self.record("tool_call", f"$ {command}", role="assistant", data={"event": event_type, "item_id": item_id, "status": status})
            return
        output = str(item.get("aggregated_output") or "")
        previous = self.item_text_by_id.get(item_id, "")
        if output.startswith(previous):
            delta = output[len(previous) :]
        else:
            delta = output
        self.item_text_by_id[item_id] = output
        exit_code = item.get("exit_code")
        body = delta or f"status={status}"
        if event_type == "item.completed":
            body = f"{body}\nexit_code={exit_code} status={status}".strip()
        self.record("tool_output", body, role="assistant", data={"event": event_type, "item_id": item_id, "status": status, "exit_code": exit_code})

    def _handle_mcp_tool_call(self, item: dict[str, Any], event_type: str, item_id: str) -> None:
        name = ".".join(part for part in (item.get("server"), item.get("tool")) if part)
        status = _status(item.get("status"))
        if event_type == "item.started":
            arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            self.record("tool_call", f"{name} {_json_text(arguments)}".strip(), role="assistant", data={"event": event_type, "item_id": item_id, "status": status})
            return
        if item.get("error"):
            text = f"{name} failed: {_json_text(item.get('error'))}"
            record_type = "error"
        else:
            text = f"{name} {status}: {_json_text(item.get('result') or {})}"
            record_type = "tool_output"
        self.record(record_type, text, role="assistant", data={"event": event_type, "item_id": item_id, "status": status})


class ChatRunner:
    def __init__(
        self,
        *,
        store: ChatStore | None = None,
        codex_bin: str | None = None,
        cwd: str | Path | None = None,
        thread_id: str | None = None,
        extra_args: list[str] | None = None,
        poll_interval: float = 1.0,
        require_live_tui_for_thread: bool = True,
        allow_detached_thread_resume: bool = False,
    ):
        self.store = store or ChatStore()
        self.codex_bin = codex_bin
        self.cwd = Path(cwd or os.environ.get("OMNIDOER_CHAT_RUNNER_CWD") or os.getcwd())
        self.thread_id = thread_id or os.environ.get("OMNIDOER_CHAT_THREAD_ID")
        self.extra_args = extra_args if extra_args is not None else shlex.split(os.environ.get("OMNIDOER_CHAT_CODEX_ARGS", ""))
        self.poll_interval = poll_interval
        self.require_live_tui_for_thread = require_live_tui_for_thread
        self.allow_detached_thread_resume = allow_detached_thread_resume

    def run_once(self) -> ChatMessage | None:
        if live_tui_bridge_active():
            return None
        if live_tui_session_active(self.thread_id):
            return None
        if self.thread_id and self.require_live_tui_for_thread and not self.allow_detached_thread_resume:
            return None
        user_message = self.store.next_user_message(claim=True)
        if user_message is None:
            return None
        assistant = self.store.append(
            role="assistant",
            text="",
            status="streaming",
            source="codex_exec",
            reply_to_message_id=user_message.message_id,
        )
        bridge = CodexJsonEventBridge(self.store, assistant)
        codex = find_codex_binary(self.codex_bin)
        if not codex:
            bridge.record("error", "Codex CLI binary was not found; cannot process Control Client chat.", role="system")
            self.store.complete(user_message.message_id)
            return self.store.complete(assistant.message_id, text="Codex CLI binary was not found.")
        if self.thread_id:
            bridge.record("status", f"Resuming Codex thread {self.thread_id} in {self.cwd}", role="system")
        else:
            bridge.record("status", f"Launching Codex JSON stream in {self.cwd}", role="system")
        image_args = []
        for image_path in image_attachment_paths(user_message.attachments):
            image_args.extend(["--image", image_path])
        if self.thread_id:
            command = [
                codex,
                "exec",
                "resume",
                "--json",
                "--cd",
                str(self.cwd),
                "--skip-git-repo-check",
                *image_args,
                *self.extra_args,
                self.thread_id,
                user_message.text,
            ]
        else:
            command = [
                codex,
                "exec",
                "--json",
                "--cd",
                str(self.cwd),
                "--skip-git-repo-check",
                *image_args,
                *self.extra_args,
                "--",
                user_message.text,
            ]
        env = self._subprocess_env()
        try:
            with subprocess.Popen(
                command,
                cwd=self.cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._handle_process_line(line, bridge)
                return_code = proc.wait()
        except Exception as exc:
            bridge.record("error", f"Codex JSON runner failed: {type(exc).__name__}", role="system")
            self.store.complete(user_message.message_id)
            return self.store.complete(assistant.message_id, text=f"Codex JSON runner failed: {type(exc).__name__}")
        if return_code != 0:
            bridge.record("error", f"Codex process exited with code {return_code}.", role="system")
        self.store.complete(user_message.message_id)
        return self.store.complete(assistant.message_id)

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stop = stop_event or threading.Event()
        while not stop.is_set():
            processed = self.run_once()
            if processed is None:
                stop.wait(max(0.1, self.poll_interval))

    def _handle_process_line(self, line: str, bridge: CodexJsonEventBridge) -> None:
        text = line.rstrip("\n")
        if not text:
            return
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            bridge.record("note", text, role="system", data={"event": "stdout"})
            return
        if isinstance(event, dict):
            bridge.handle(event)
        else:
            bridge.record("note", _json_text(event), role="system", data={"event": "stdout"})

    def _subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("OMNIDOER_CONSOLE", "1")
        env.setdefault("OMNIDOER_CODEX_BRAND", "omnidoer")
        env.setdefault("CODEX_CLI_BRAND", "omnidoer")
        return env


def start_chat_runner_thread(
    *,
    codex_bin: str | None = None,
    cwd: str | Path | None = None,
    thread_id: str | None = None,
    extra_args: list[str] | None = None,
    poll_interval: float = 1.0,
    require_live_tui_for_thread: bool = True,
    allow_detached_thread_resume: bool = False,
) -> threading.Thread:
    runner = ChatRunner(
        codex_bin=codex_bin,
        cwd=cwd,
        thread_id=thread_id,
        extra_args=extra_args,
        poll_interval=poll_interval,
        require_live_tui_for_thread=require_live_tui_for_thread,
        allow_detached_thread_resume=allow_detached_thread_resume,
    )
    thread = threading.Thread(target=runner.run_forever, name="omnidoer-chat-runner", daemon=True)
    thread.start()
    return thread

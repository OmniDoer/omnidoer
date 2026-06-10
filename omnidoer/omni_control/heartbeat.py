"""Idle heartbeat scheduler for queued OmniDoer Control Client work."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from omnidoer.omni_control.chat import (
    DEFAULT_CHAT_SESSION_ID,
    ChatStore,
    validate_chat_session_id,
)
from omnidoer.omni_control.pairing import parse_duration_seconds
from omnidoer.omni_control.state_io import atomic_write_json, locked_state_file
from omnidoer.paths import state_file


HEARTBEAT_STATE_FILE = "control_heartbeat.json"
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 60 * 60
DEFAULT_HEARTBEAT_MIN_IDLE_SECONDS = 5 * 60
DEFAULT_HEARTBEAT_POLL_SECONDS = 30.0
ACTIVE_CHAT_STATUSES = {"queued", "claimed", "streaming"}
SKIP_STATE_WRITE_MIN_SECONDS = 5 * 60


@dataclass
class HeartbeatState:
    enabled: bool = False
    interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS
    min_idle_seconds: float = DEFAULT_HEARTBEAT_MIN_IDLE_SECONDS
    heartbeat_file: str = ""
    session_id: str = DEFAULT_CHAT_SESSION_ID
    last_triggered_at: float | None = None
    last_message_id: str | None = None
    last_skipped_at: float | None = None
    last_skip_reason: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["secret_fields_allowed"] = False
        payload["control_client_calls_model"] = False
        return payload


def heartbeat_state_path(path: Path | None = None) -> Path:
    return path or state_file(HEARTBEAT_STATE_FILE)


def default_heartbeat_file(*, cwd: str | Path | None = None) -> Path:
    configured = os.environ.get("OMNIDOER_HEARTBEAT_FILE")
    candidates = [
        Path(configured).expanduser() if configured else None,
        Path(cwd).expanduser() / "HEARTBEAT.md" if cwd else None,
        Path.cwd() / "HEARTBEAT.md",
        state_file("HEARTBEAT.md"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate.resolve()
    if cwd:
        return (Path(cwd).expanduser() / "HEARTBEAT.md").resolve()
    return (Path.cwd() / "HEARTBEAT.md").resolve()


def _load_state(path: Path, *, cwd: str | Path | None = None) -> HeartbeatState:
    now = time.time()
    if not path.exists():
        return HeartbeatState(
            heartbeat_file=str(default_heartbeat_file(cwd=cwd)),
            created_at=now,
            updated_at=now,
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    state = HeartbeatState(**raw)
    if not state.heartbeat_file:
        state.heartbeat_file = str(default_heartbeat_file(cwd=cwd))
    state.session_id = validate_chat_session_id(state.session_id)
    return state


def load_heartbeat_state(
    *, state_path: Path | None = None, cwd: str | Path | None = None
) -> HeartbeatState:
    path = heartbeat_state_path(state_path)
    with locked_state_file(path):
        return _load_state(path, cwd=cwd)


def save_heartbeat_state(
    state: HeartbeatState, *, state_path: Path | None = None
) -> HeartbeatState:
    path = heartbeat_state_path(state_path)
    state.session_id = validate_chat_session_id(state.session_id)
    state.updated_at = time.time()
    if not state.created_at:
        state.created_at = state.updated_at
    with locked_state_file(path):
        atomic_write_json(path, asdict(state))
    return state


def configure_heartbeat(
    *,
    enabled: bool | None = None,
    interval: str | float | int | None = None,
    min_idle: str | float | int | None = None,
    heartbeat_file: str | Path | None = None,
    session_id: str | None = None,
    state_path: Path | None = None,
    cwd: str | Path | None = None,
) -> HeartbeatState:
    path = heartbeat_state_path(state_path)
    with locked_state_file(path):
        state = _load_state(path, cwd=cwd)
        if enabled is not None:
            state.enabled = bool(enabled)
        if interval is not None:
            state.interval_seconds = max(1.0, parse_duration_seconds(str(interval)))
        if min_idle is not None:
            state.min_idle_seconds = max(0.0, parse_duration_seconds(str(min_idle)))
        if heartbeat_file is not None:
            state.heartbeat_file = str(Path(heartbeat_file).expanduser().resolve())
        if session_id is not None:
            state.session_id = validate_chat_session_id(session_id)
        state.updated_at = time.time()
        if not state.created_at:
            state.created_at = state.updated_at
        atomic_write_json(path, asdict(state))
        return state


def _read_heartbeat_file(path: str | Path) -> str:
    target = Path(path).expanduser()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    return target.read_text(encoding="utf-8").strip()


def _format_heartbeat_prompt(
    *, heartbeat_file: str, instructions: str, now: float
) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(now))
    return "\n".join(
        [
            "[OmniDoer heartbeat]",
            f"触发时间: {stamp}",
            f"任务文件: {heartbeat_file}",
            "",
            "请在空闲心跳中执行以下 HEARTBEAT.md 任务清单。遵守任务中的登记标准；如果没有达到阈值的新发现，只更新归档或说明本次无重大新增。",
            "",
            instructions,
        ]
    )


def _latest_chat_activity(store: ChatStore) -> float | None:
    timestamps: list[float] = []
    for message in store.list(limit=1000):
        timestamps.append(float(message.updated_at or message.created_at or 0.0))
    for record in store.list_records(limit=1000):
        timestamps.append(float(record.created_at or 0.0))
    timestamps = [value for value in timestamps if value > 0]
    return max(timestamps) if timestamps else None


def chat_session_idle(
    *,
    store: ChatStore,
    min_idle_seconds: float,
    now: float | None = None,
) -> tuple[bool, str, float | None]:
    current = now or time.time()
    for message in store.list(limit=1000):
        if message.status in ACTIVE_CHAT_STATUSES:
            age = current - float(message.updated_at or message.created_at or current)
            return False, f"active_{message.status}_message", age
    latest = _latest_chat_activity(store)
    if latest is not None and current - latest < min_idle_seconds:
        return False, "recent_chat_activity", current - latest
    return True, "idle", (current - latest) if latest is not None else None


class HeartbeatRunner:
    def __init__(
        self,
        *,
        state_path: Path | None = None,
        cwd: str | Path | None = None,
        poll_interval: float = DEFAULT_HEARTBEAT_POLL_SECONDS,
    ):
        self.state_path = heartbeat_state_path(state_path)
        self.cwd = cwd
        self.poll_interval = max(1.0, float(poll_interval))

    def status(self) -> dict[str, Any]:
        state = load_heartbeat_state(state_path=self.state_path, cwd=self.cwd)
        store = ChatStore(session_id=state.session_id)
        idle, reason, idle_seconds = chat_session_idle(
            store=store,
            min_idle_seconds=state.min_idle_seconds,
        )
        payload = state.to_public_dict()
        payload.update(
            {
                "idle": idle,
                "idle_reason": reason,
                "idle_seconds": idle_seconds,
                "heartbeat_file_exists": Path(state.heartbeat_file)
                .expanduser()
                .is_file(),
            }
        )
        return payload

    def run_once(self, *, force: bool = False) -> dict[str, Any]:
        now = time.time()
        state = load_heartbeat_state(state_path=self.state_path, cwd=self.cwd)
        if not state.enabled and not force:
            return self._record_skip(state, "disabled", now)
        elapsed = now - float(state.last_triggered_at or 0.0)
        if (
            not force
            and state.last_triggered_at is not None
            and elapsed < state.interval_seconds
        ):
            return self._record_skip(state, "interval_not_elapsed", now)
        store = ChatStore(session_id=state.session_id)
        idle, reason, idle_seconds = chat_session_idle(
            store=store,
            min_idle_seconds=state.min_idle_seconds,
            now=now,
        )
        if not idle and not force:
            return self._record_skip(state, reason, now, idle_seconds=idle_seconds)
        try:
            instructions = _read_heartbeat_file(state.heartbeat_file)
        except FileNotFoundError:
            return self._record_skip(state, "heartbeat_file_not_found", now)
        if not instructions:
            return self._record_skip(state, "heartbeat_file_empty", now)
        message = store.append(
            role="user",
            text=_format_heartbeat_prompt(
                heartbeat_file=state.heartbeat_file,
                instructions=instructions,
                now=now,
            ),
            source="heartbeat",
            client_message_id=f"control_heartbeat_{int(now)}_{uuid.uuid4().hex[:8]}",
        )
        store.append_record(
            record_type="status",
            text="Heartbeat task queued for the idle agent.",
            role="system",
            message_id=message.message_id,
            source="heartbeat",
            data={
                "heartbeat_file": state.heartbeat_file,
                "interval_seconds": state.interval_seconds,
                "min_idle_seconds": state.min_idle_seconds,
                "forced": force,
            },
        )
        state.last_triggered_at = now
        state.last_message_id = message.message_id
        state.last_skip_reason = None
        save_heartbeat_state(state, state_path=self.state_path)
        return {
            "status": "queued",
            "message_id": message.message_id,
            "session_id": state.session_id,
            "heartbeat_file": state.heartbeat_file,
            "secret_fields_allowed": False,
            "control_client_calls_model": False,
        }

    def _record_skip(
        self,
        state: HeartbeatState,
        reason: str,
        now: float,
        *,
        idle_seconds: float | None = None,
    ) -> dict[str, Any]:
        if (
            state.last_skip_reason == reason
            and state.last_skipped_at is not None
            and now - state.last_skipped_at < SKIP_STATE_WRITE_MIN_SECONDS
        ):
            return {
                "status": "skipped",
                "reason": reason,
                "idle_seconds": idle_seconds,
                "secret_fields_allowed": False,
                "control_client_calls_model": False,
            }
        state.last_skipped_at = now
        state.last_skip_reason = reason
        save_heartbeat_state(state, state_path=self.state_path)
        return {
            "status": "skipped",
            "reason": reason,
            "idle_seconds": idle_seconds,
            "secret_fields_allowed": False,
            "control_client_calls_model": False,
        }

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stop = stop_event or threading.Event()
        while not stop.is_set():
            self.run_once()
            stop.wait(self.poll_interval)


def start_heartbeat_thread(
    *,
    cwd: str | Path | None = None,
    poll_interval: float = DEFAULT_HEARTBEAT_POLL_SECONDS,
) -> threading.Thread:
    runner = HeartbeatRunner(cwd=cwd, poll_interval=poll_interval)
    thread = threading.Thread(
        target=runner.run_forever, name="omnidoer-heartbeat", daemon=True
    )
    thread.start()
    return thread


def format_heartbeat_status_text(status: dict[str, Any]) -> str:
    enabled = "yes" if status.get("enabled") else "no"
    idle = "yes" if status.get("idle") else "no"
    lines = [
        "OmniDoer heartbeat",
        f"Enabled: {enabled}",
        f"Idle now: {idle} ({status.get('idle_reason') or 'unknown'})",
        f"Session: {status.get('session_id') or DEFAULT_CHAT_SESSION_ID}",
        f"Interval seconds: {status.get('interval_seconds')}",
        f"Minimum idle seconds: {status.get('min_idle_seconds')}",
        f"HEARTBEAT.md: {status.get('heartbeat_file')}",
        f"File exists: {'yes' if status.get('heartbeat_file_exists') else 'no'}",
        f"Last triggered at: {status.get('last_triggered_at') or 'never'}",
        f"Last message id: {status.get('last_message_id') or 'none'}",
        f"Last skip reason: {status.get('last_skip_reason') or 'none'}",
        "Secret exposure: false",
    ]
    return "\n".join(lines)


def heartbeat_command_text(args: list[str], *, cwd: str | Path | None = None) -> str:
    subcommand = args[1].lower() if len(args) > 1 else "status"
    runner = HeartbeatRunner(cwd=cwd)
    if subcommand in {"status", "show"}:
        return format_heartbeat_status_text(runner.status())
    if subcommand in {"enable", "on", "start"}:
        interval = args[2] if len(args) > 2 else None
        state = configure_heartbeat(enabled=True, interval=interval, cwd=cwd)
        return (
            format_heartbeat_status_text(HeartbeatRunner(cwd=cwd).status())
            + f"\nUpdated: enabled heartbeat every {state.interval_seconds:g}s"
        )
    if subcommand in {"disable", "off", "stop"}:
        configure_heartbeat(enabled=False, cwd=cwd)
        return (
            format_heartbeat_status_text(HeartbeatRunner(cwd=cwd).status())
            + "\nUpdated: disabled"
        )
    if subcommand in {"run", "run-once", "trigger"}:
        result = runner.run_once(force="--force" in args[2:])
        return "\n".join(
            [
                "OmniDoer heartbeat run-once",
                json.dumps(result, ensure_ascii=False, sort_keys=True),
                "Secret exposure: false",
            ]
        )
    return "\n".join(
        [
            "Usage: /heartbeat [status|enable [interval]|disable|run [--force]]",
            "Secret exposure: false",
            "Model submission: false",
        ]
    )

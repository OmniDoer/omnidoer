"""Idle heartbeat scheduler for queued OmniDoer Control Client work."""

from __future__ import annotations

import json
import datetime as dt
import os
import random
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
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
HEARTBEAT_TASKS_FILE = "control_heartbeat_tasks.json"
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 60 * 60
DEFAULT_HEARTBEAT_MIN_IDLE_SECONDS = 5 * 60
DEFAULT_HEARTBEAT_POLL_SECONDS = 30.0
ACTIVE_CHAT_STATUSES = {"queued", "claimed", "streaming"}
STALE_NON_USER_ACTIVE_SECONDS = 30 * 60
SKIP_STATE_WRITE_MIN_SECONDS = 5 * 60
MAX_HEARTBEAT_TASK_TEXT_LENGTH = 8000
MAX_HEARTBEAT_TASK_TITLE_LENGTH = 120
HEARTBEAT_TASK_POSITIONS = {"random", "front", "back"}
SECONDS_PER_DAY = 24 * 60 * 60


@dataclass
class HeartbeatTask:
    task_id: str
    text: str
    title: str = ""
    source: str = "control_client"
    enabled: bool = True
    weight: int = 1
    priority: str = ""
    quota: str = ""
    repo_path: str = ""
    remote_url: str = ""
    target: str = ""
    deadline_utc: str = ""
    min_interval_seconds: float | None = None
    interrupt_active: bool = True
    created_at: float = 0.0
    updated_at: float = 0.0
    last_triggered_at: float | None = None
    trigger_count: int = 0

    def to_public_dict(self, *, now: float | None = None) -> dict[str, Any]:
        payload = asdict(self)
        current = time.time() if now is None else now
        payload["effective_weight"] = effective_task_weight(self, current)
        payload["due_at"] = task_due_at(self)
        payload["seconds_until_due"] = seconds_until_due(self, current)
        payload["deadline_seconds_remaining"] = deadline_seconds_remaining(self, current)
        payload["secret_fields_allowed"] = False
        payload["control_client_calls_model"] = False
        payload["submitted_to_openai_api_by_control_client"] = False
        return payload


@dataclass
class HeartbeatTaskQueue:
    order: list[str] = field(default_factory=list)
    tasks: dict[str, HeartbeatTask] = field(default_factory=dict)
    cursor: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_public_dict(self) -> dict[str, Any]:
        now = time.time()
        tasks = [self.tasks[task_id].to_public_dict(now=now) for task_id in self.order if task_id in self.tasks]
        return {
            "order": list(self.order),
            "cursor": self.cursor,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tasks": tasks,
            "enabled_count": sum(1 for task in tasks if task.get("enabled")),
            "secret_fields_allowed": False,
            "control_client_calls_model": False,
        }


@dataclass
class HeartbeatState:
    enabled: bool = False
    interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS
    min_idle_seconds: float = DEFAULT_HEARTBEAT_MIN_IDLE_SECONDS
    heartbeat_file: str = ""
    task_queue_file: str = ""
    session_id: str = DEFAULT_CHAT_SESSION_ID
    last_triggered_at: float | None = None
    last_message_id: str | None = None
    last_task_id: str | None = None
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


def heartbeat_tasks_path(path: Path | None = None) -> Path:
    return path or state_file(HEARTBEAT_TASKS_FILE)


def _task_from_payload(payload: dict[str, Any]) -> HeartbeatTask:
    fields = HeartbeatTask.__dataclass_fields__
    return HeartbeatTask(**{key: value for key, value in payload.items() if key in fields})


def parse_deadline_timestamp(value: str | None) -> float | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            parsed = dt.datetime.fromisoformat(text[:-1] + "+00:00")
        else:
            parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).timestamp()


def deadline_seconds_remaining(task: HeartbeatTask, now: float | None = None) -> float | None:
    deadline = parse_deadline_timestamp(task.deadline_utc)
    if deadline is None:
        return None
    return deadline - (time.time() if now is None else now)


def deadline_weight_bonus(task: HeartbeatTask, now: float | None = None) -> int:
    remaining = deadline_seconds_remaining(task, now)
    if remaining is None:
        return 0
    if remaining <= 0:
        return 100
    days = remaining / SECONDS_PER_DAY
    if days <= 3:
        return 24
    if days <= 7:
        return 16
    if days <= 14:
        return 10
    if days <= 30:
        return 7
    if days <= 60:
        return 4
    if days <= 120:
        return 2
    return 1


def effective_task_weight(task: HeartbeatTask, now: float | None = None) -> int:
    return max(1, int(task.weight)) + deadline_weight_bonus(task, now)


def task_due_at(task: HeartbeatTask) -> float | None:
    if task.min_interval_seconds is None:
        return None
    if task.last_triggered_at is None:
        return 0.0
    return float(task.last_triggered_at) + max(1.0, float(task.min_interval_seconds))


def seconds_until_due(task: HeartbeatTask, now: float | None = None) -> float | None:
    due_at = task_due_at(task)
    if due_at is None:
        return None
    return max(0.0, due_at - (time.time() if now is None else now))


def task_is_due(task: HeartbeatTask, now: float | None = None) -> bool:
    wait = seconds_until_due(task, now)
    return wait is None or wait <= 0.0


def task_overdue_seconds(task: HeartbeatTask, now: float | None = None) -> float:
    due_at = task_due_at(task)
    if due_at is None:
        return 0.0
    return max(0.0, (time.time() if now is None else now) - due_at)


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
            task_queue_file=str(heartbeat_tasks_path()),
            created_at=now,
            updated_at=now,
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    fields = HeartbeatState.__dataclass_fields__
    state = HeartbeatState(**{key: value for key, value in raw.items() if key in fields})
    if not state.heartbeat_file:
        state.heartbeat_file = str(default_heartbeat_file(cwd=cwd))
    if not state.task_queue_file:
        state.task_queue_file = str(heartbeat_tasks_path())
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
        if not state.task_queue_file:
            state.task_queue_file = str(heartbeat_tasks_path())
        state.updated_at = time.time()
        if not state.created_at:
            state.created_at = state.updated_at
        atomic_write_json(path, asdict(state))
        return state


class HeartbeatTaskStore:
    def __init__(self, path: Path | None = None):
        self.path = heartbeat_tasks_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_payload(self) -> HeartbeatTaskQueue:
        if not self.path.exists():
            now = time.time()
            return HeartbeatTaskQueue(created_at=now, updated_at=now)
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "tasks" in raw:
            raw_tasks = raw.get("tasks") or {}
            if isinstance(raw_tasks, list):
                tasks = {item["task_id"]: _task_from_payload(item) for item in raw_tasks}
            else:
                tasks = {
                    key: _task_from_payload(value)
                    for key, value in raw_tasks.items()
                }
            order = [
                str(task_id)
                for task_id in (raw.get("order") or [])
                if str(task_id) in tasks
            ]
            for task in sorted(tasks.values(), key=lambda item: item.created_at):
                if task.task_id not in order:
                    order.append(task.task_id)
            return HeartbeatTaskQueue(
                order=order,
                tasks=tasks,
                cursor=int(raw.get("cursor") or 0),
                created_at=float(raw.get("created_at") or 0.0),
                updated_at=float(raw.get("updated_at") or 0.0),
            )
        tasks = {key: _task_from_payload(value) for key, value in raw.items()}
        order = [task.task_id for task in sorted(tasks.values(), key=lambda item: item.created_at)]
        return HeartbeatTaskQueue(order=order, tasks=tasks)

    def _save_payload(self, queue: HeartbeatTaskQueue) -> None:
        now = time.time()
        if not queue.created_at:
            queue.created_at = now
        queue.updated_at = now
        queue.order = [task_id for task_id in queue.order if task_id in queue.tasks]
        payload = {
            "order": queue.order,
            "cursor": queue.cursor,
            "created_at": queue.created_at,
            "updated_at": queue.updated_at,
            "tasks": {
                task_id: asdict(task)
                for task_id, task in queue.tasks.items()
            },
        }
        atomic_write_json(self.path, payload)

    def status(self) -> dict[str, Any]:
        with locked_state_file(self.path):
            queue = self._load_payload()
        payload = queue.to_public_dict()
        payload["path"] = str(self.path)
        return payload

    def list(self, *, include_disabled: bool = True) -> list[HeartbeatTask]:
        with locked_state_file(self.path):
            queue = self._load_payload()
        tasks = [queue.tasks[task_id] for task_id in queue.order if task_id in queue.tasks]
        if include_disabled:
            return tasks
        return [task for task in tasks if task.enabled]

    def create(
        self,
        text: str,
        *,
        title: str | None = None,
        source: str = "control_client",
        weight: int = 1,
        position: str = "random",
        priority: str = "",
        quota: str = "",
        repo_path: str = "",
        remote_url: str = "",
        target: str = "",
        deadline_utc: str = "",
        min_interval_seconds: float | None = None,
        interrupt_active: bool = True,
    ) -> HeartbeatTask:
        cleaned = str(text or "").strip()
        if not cleaned:
            raise ValueError("heartbeat task text is required")
        if len(cleaned) > MAX_HEARTBEAT_TASK_TEXT_LENGTH:
            raise ValueError("heartbeat task text is too long")
        normalized_position = position if position in HEARTBEAT_TASK_POSITIONS else "random"
        with locked_state_file(self.path):
            queue = self._load_payload()
            now = time.time()
            task = HeartbeatTask(
                task_id=f"hbt_{uuid.uuid4().hex}",
                text=cleaned,
                title=str(title or "").strip()[:MAX_HEARTBEAT_TASK_TITLE_LENGTH],
                source=source,
                weight=max(1, int(weight)),
                priority=str(priority or "").strip(),
                quota=str(quota or "").strip(),
                repo_path=str(repo_path or "").strip(),
                remote_url=str(remote_url or "").strip(),
                target=str(target or "").strip(),
                deadline_utc=str(deadline_utc or "").strip(),
                min_interval_seconds=(
                    None
                    if min_interval_seconds is None
                    else max(1.0, float(min_interval_seconds))
                ),
                interrupt_active=bool(interrupt_active),
                created_at=now,
                updated_at=now,
            )
            queue.tasks[task.task_id] = task
            if normalized_position == "front":
                index = 0
            elif normalized_position == "back":
                index = len(queue.order)
            else:
                index = random.randrange(len(queue.order) + 1)
            queue.order.insert(index, task.task_id)
            if index <= queue.cursor:
                queue.cursor += 1
            self._save_payload(queue)
            return task

    def set_enabled(self, task_id: str, enabled: bool) -> HeartbeatTask:
        with locked_state_file(self.path):
            queue = self._load_payload()
            task = queue.tasks[task_id]
            task.enabled = bool(enabled)
            task.updated_at = time.time()
            queue.tasks[task.task_id] = task
            self._save_payload(queue)
            return task

    def remove(self, task_id: str) -> HeartbeatTask:
        with locked_state_file(self.path):
            queue = self._load_payload()
            task = queue.tasks.pop(task_id)
            removed_before_cursor = [
                index
                for index, item in enumerate(queue.order)
                if item == task_id and index < queue.cursor
            ]
            queue.order = [item for item in queue.order if item != task_id]
            if removed_before_cursor:
                queue.cursor = max(0, queue.cursor - len(removed_before_cursor))
            self._save_payload(queue)
            return task

    def next_task(self, *, now: float | None = None, consume: bool = True) -> HeartbeatTask | None:
        with locked_state_file(self.path):
            queue = self._load_payload()
            current = now or time.time()
            fixed_due = [
                task
                for task_id in queue.order
                if (task := queue.tasks.get(task_id))
                and task.enabled
                and task.min_interval_seconds is not None
                and task_is_due(task, current)
            ]
            if fixed_due:
                task = max(
                    fixed_due,
                    key=lambda item: (
                        task_overdue_seconds(item, current),
                        effective_task_weight(item, current),
                        -queue.order.index(item.task_id),
                    ),
                )
                if consume:
                    task.last_triggered_at = current
                    task.trigger_count += 1
                    task.updated_at = current
                    queue.tasks[task.task_id] = task
                    self._save_payload(queue)
                return task

            ring: list[str] = []
            for task_id in queue.order:
                task = queue.tasks.get(task_id)
                if not task or not task.enabled:
                    continue
                if not task_is_due(task, current):
                    continue
                ring.extend([task_id] * effective_task_weight(task, current))
            if not ring:
                return None
            index = int(queue.cursor or 0) % len(ring)
            task = queue.tasks[ring[index]]
            if consume:
                task.last_triggered_at = current
                task.trigger_count += 1
                task.updated_at = current
                queue.tasks[task.task_id] = task
                queue.cursor = (index + 1) % len(ring)
                self._save_payload(queue)
            return task


def _read_heartbeat_file(path: str | Path) -> str:
    target = Path(path).expanduser()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    return target.read_text(encoding="utf-8").strip()


def _format_heartbeat_prompt(
    *,
    heartbeat_file: str,
    instructions: str,
    now: float,
    task: HeartbeatTask | None = None,
) -> str:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(now))
    lines = [
        "[OmniDoer heartbeat]",
        f"触发时间: {stamp}",
    ]
    if task is not None:
        metadata_lines = [
            f"任务优先级: {task.priority}",
            f"任务配额: {task.quota}",
            f"任务仓库: {task.repo_path}",
            f"任务远端: {task.remote_url}",
            f"任务目标: {task.target}",
            f"任务截止时间: {task.deadline_utc}",
            f"任务最小触发间隔秒: {task.min_interval_seconds}",
        ]
        metadata_lines = [line for line in metadata_lines if not line.endswith(": ") and not line.endswith(": None")]
        lines.extend(
            [
                "任务来源: heartbeat queue",
                f"任务ID: {task.task_id}",
                f"任务标题: {task.title or '(untitled)'}",
                f"任务权重: {task.weight}",
                f"任务有效权重: {effective_task_weight(task, now)}",
                *metadata_lines,
                "",
                "请执行这个由持久 heartbeat 队列轮询选出的任务。完成后在回复中说明本轮处理的任务ID、关键证据、下一步以及是否需要继续排队；不要依赖聊天记忆来判断还有哪些长期任务。",
                "",
                instructions,
            ]
        )
    else:
        lines.extend(
            [
                f"任务文件: {heartbeat_file}",
                "",
                "请在空闲心跳中执行以下 HEARTBEAT.md 任务清单。遵守任务中的登记标准；如果没有达到阈值的新发现，只更新归档或说明本次无重大新增。",
                "",
                instructions,
            ]
        )
    return "\n".join(lines)


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
    stale_non_user_active_seconds: float = STALE_NON_USER_ACTIVE_SECONDS,
) -> tuple[bool, str, float | None]:
    current = now or time.time()
    for message in store.list(limit=1000):
        if message.status in ACTIVE_CHAT_STATUSES:
            age = current - float(message.updated_at or message.created_at or current)
            if message.role != "user" and age >= stale_non_user_active_seconds:
                continue
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
        task_store = HeartbeatTaskStore(Path(state.task_queue_file))
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
                "task_queue": task_store.status(),
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
        task_store = HeartbeatTaskStore(Path(state.task_queue_file))
        try:
            pending_task = task_store.next_task(now=now, consume=False)
        except Exception:
            pending_task = None
        if pending_task is None or (not pending_task.interrupt_active and not force):
            idle, reason, idle_seconds = chat_session_idle(
                store=store,
                min_idle_seconds=state.min_idle_seconds,
                now=now,
            )
            if not idle and not force:
                return self._record_skip(state, reason, now, idle_seconds=idle_seconds)
        try:
            task = task_store.next_task(now=now)
        except Exception:
            task = None
        if pending_task is not None and task is None:
            return self._record_skip(state, "no_due_heartbeat_task", now)
        if task is None:
            try:
                instructions = _read_heartbeat_file(state.heartbeat_file)
            except FileNotFoundError:
                return self._record_skip(state, "heartbeat_file_not_found", now)
        else:
            instructions = task.text
        if not instructions:
            return self._record_skip(state, "heartbeat_file_empty", now)
        message = store.append(
            role="user",
            text=_format_heartbeat_prompt(
                heartbeat_file=state.heartbeat_file,
                instructions=instructions,
                now=now,
                task=task,
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
                "heartbeat_task_id": task.task_id if task else None,
                "heartbeat_task_title": task.title if task else None,
                "heartbeat_task_queue_file": state.task_queue_file,
                "interval_seconds": state.interval_seconds,
                "min_idle_seconds": state.min_idle_seconds,
                "forced": force,
            },
        )
        state.last_triggered_at = now
        state.last_message_id = message.message_id
        state.last_task_id = task.task_id if task else None
        state.last_skip_reason = None
        save_heartbeat_state(state, state_path=self.state_path)
        return {
            "status": "queued",
            "message_id": message.message_id,
            "session_id": state.session_id,
            "heartbeat_file": state.heartbeat_file,
            "heartbeat_task_id": task.task_id if task else None,
            "heartbeat_task_title": task.title if task else None,
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
    task_queue = status.get("task_queue") if isinstance(status.get("task_queue"), dict) else {}
    task_count = len(task_queue.get("tasks") or [])
    lines = [
        "OmniDoer heartbeat",
        f"Enabled: {enabled}",
        f"Idle now: {idle} ({status.get('idle_reason') or 'unknown'})",
        f"Session: {status.get('session_id') or DEFAULT_CHAT_SESSION_ID}",
        f"Interval seconds: {status.get('interval_seconds')}",
        f"Minimum idle seconds: {status.get('min_idle_seconds')}",
        f"HEARTBEAT.md: {status.get('heartbeat_file')}",
        f"File exists: {'yes' if status.get('heartbeat_file_exists') else 'no'}",
        f"Task queue: {task_queue.get('path') or status.get('task_queue_file') or 'default'}",
        f"Queued heartbeat tasks: {task_count} ({task_queue.get('enabled_count') or 0} enabled)",
        f"Task cursor: {task_queue.get('cursor', 0)}",
        f"Last task id: {status.get('last_task_id') or 'none'}",
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
    if subcommand in {"tasks", "list"}:
        tasks = HeartbeatTaskStore().list(include_disabled=True)
        lines = ["OmniDoer heartbeat tasks"]
        if not tasks:
            lines.append("(empty)")
        for task in tasks:
            enabled = "enabled" if task.enabled else "disabled"
            title = task.title or task.text.splitlines()[0][:80]
            lines.append(
                f"- {task.task_id} [{enabled}] weight={task.weight} runs={task.trigger_count}: {title}"
            )
        lines.append("Secret exposure: false")
        lines.append("Model submission: false")
        return "\n".join(lines)
    if subcommand in {"add", "queue"}:
        text = " ".join(args[2:]).strip()
        if not text:
            return "Usage: /heartbeat add <task text>\nSecret exposure: false\nModel submission: false"
        task = HeartbeatTaskStore().create(text, source="control_client", position="random")
        return "\n".join(
            [
                "Heartbeat task queued.",
                f"Task id: {task.task_id}",
                f"Weight: {task.weight}",
                "Insertion: random",
                "Secret exposure: false",
                "Model submission: false",
            ]
        )
    if subcommand in {"remove", "delete"}:
        if len(args) < 3:
            return "Usage: /heartbeat remove <task_id>\nSecret exposure: false\nModel submission: false"
        task = HeartbeatTaskStore().remove(args[2])
        return "\n".join(
            [
                "Heartbeat task removed.",
                f"Task id: {task.task_id}",
                "Secret exposure: false",
                "Model submission: false",
            ]
        )
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
            "Usage: /heartbeat [status|tasks|add <task>|remove <task_id>|enable [interval]|disable|run [--force]]",
            "Secret exposure: false",
            "Model submission: false",
        ]
    )

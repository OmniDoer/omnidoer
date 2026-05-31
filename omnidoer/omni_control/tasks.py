"""Local task queue for Control Client initiated Codex work."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from omnidoer.omni_control.state_io import atomic_write_json, locked_state_file
from omnidoer.paths import state_file


TASK_STATUSES = {"pending", "claimed", "completed", "cancelled"}


@dataclass
class UserTask:
    task_id: str
    text: str
    source: str = "control_client"
    status: str = "pending"
    created_at: float = 0.0
    updated_at: float = 0.0
    claimed_at: float | None = None
    completed_at: float | None = None

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["secret_fields_allowed"] = False
        data["submitted_to_openai_api_by_control_client"] = False
        data["delivered_to_codex_via_mcp"] = self.status in {"claimed", "completed"}
        return data


class TaskStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_tasks.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, UserTask]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: UserTask(**value) for key, value in raw.items()}

    def _save(self, tasks: dict[str, UserTask]) -> None:
        serializable = {key: asdict(value) for key, value in tasks.items()}
        atomic_write_json(self.path, serializable)

    def list(self, include_completed: bool = False) -> list[UserTask]:
        tasks = sorted(self._load().values(), key=lambda task: task.created_at)
        if include_completed:
            return tasks
        return [task for task in tasks if task.status in {"pending", "claimed"}]

    def get(self, task_id: str) -> UserTask:
        tasks = self._load()
        try:
            return tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"task not found: {task_id}") from exc

    def create(self, text: str, source: str = "control_client") -> UserTask:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("task text is required")
        if len(cleaned) > 4000:
            raise ValueError("task text is too long")
        with locked_state_file(self.path):
            now = time.time()
            task = UserTask(
                task_id=f"task_{uuid.uuid4().hex}",
                text=cleaned,
                source=source,
                created_at=now,
                updated_at=now,
            )
            tasks = self._load()
            tasks[task.task_id] = task
            self._save(tasks)
            return task

    def next_pending(self, *, claim: bool = True) -> UserTask | None:
        with locked_state_file(self.path):
            tasks = self._load()
            pending = sorted((task for task in tasks.values() if task.status == "pending"), key=lambda task: task.created_at)
            if not pending:
                return None
            task = pending[0]
            if claim:
                now = time.time()
                task.status = "claimed"
                task.claimed_at = now
                task.updated_at = now
                tasks[task.task_id] = task
                self._save(tasks)
            return task

    def complete(self, task_id: str) -> UserTask:
        with locked_state_file(self.path):
            tasks = self._load()
            task = tasks[task_id]
            if task.status == "cancelled":
                raise ValueError("task is cancelled")
            now = time.time()
            task.status = "completed"
            task.completed_at = now
            task.updated_at = now
            tasks[task.task_id] = task
            self._save(tasks)
            return task

    def cancel(self, task_id: str) -> UserTask:
        with locked_state_file(self.path):
            tasks = self._load()
            task = tasks[task_id]
            if task.status == "completed":
                raise ValueError("task is completed")
            task.status = "cancelled"
            task.updated_at = time.time()
            tasks[task.task_id] = task
            self._save(tasks)
            return task

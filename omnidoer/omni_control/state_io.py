"""Thread-safe helpers for Control Service JSON state files."""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[Path, threading.RLock] = {}


def _normalized_path(path: Path) -> Path:
    return path.expanduser().resolve()


def _lock_for_path(path: Path) -> threading.RLock:
    normalized = _normalized_path(path)
    with _LOCKS_GUARD:
        lock = _LOCKS.get(normalized)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[normalized] = lock
        return lock


@contextmanager
def locked_state_file(path: Path) -> Iterator[None]:
    lock = _lock_for_path(path)
    with lock:
        yield


def atomic_write_json(path: Path, payload: Any, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        tmp.replace(path)
        path.chmod(mode)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass

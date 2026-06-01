"""Filesystem paths for OmniDoer local state."""

from __future__ import annotations

import os
from pathlib import Path


def home() -> Path:
    configured = os.environ.get("OMNIDOER_HOME")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".omnidoer").resolve()


def ensure_home() -> Path:
    path = home()
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def state_file(name: str) -> Path:
    return ensure_home() / name


def default_vault_path() -> Path:
    return state_file("vault.json")


def default_audit_path() -> Path:
    return state_file("audit.jsonl")

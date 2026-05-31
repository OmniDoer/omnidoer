"""Runtime metadata for the local Control Service process."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from omnidoer.omni_control.cloud import ControlServiceConfig, validate_public_url
from omnidoer.omni_control.state_io import atomic_write_json
from omnidoer.paths import home, state_file


RUNTIME_STATE_NAME = "control_service.json"
RUNTIME_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def _pid_is_running(pid: object) -> bool:
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except OSError:
        return False
    return True


def _candidate_runtime_paths() -> list[Path]:
    paths = [home() / RUNTIME_STATE_NAME]
    env_home = os.environ.get("OMNIDOER_HOME")
    if env_home:
        paths.append(Path(env_home).expanduser().resolve() / RUNTIME_STATE_NAME)
    paths.append(Path.home() / ".omnidoer" / RUNTIME_STATE_NAME)
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def record_control_service_runtime(config: ControlServiceConfig) -> dict[str, Any]:
    payload = {
        "host": config.host,
        "port": config.port,
        "public_url": config.public_url,
        "public_origin": config.public_origin,
        "mode": config.mode,
        "cloud_direct": config.cloud_direct,
        "behind_reverse_proxy": config.behind_reverse_proxy,
        "tls_enabled": bool(config.tls_cert and config.tls_key) or config.tls_self_signed_dev,
        "pid": os.getpid(),
        "updated_at": time.time(),
    }
    _atomic_write_json(state_file(RUNTIME_STATE_NAME), payload)
    return payload


def load_control_service_runtime(*, require_running: bool = True, now: float | None = None) -> dict[str, Any] | None:
    current_time = time.time() if now is None else now
    for path in _candidate_runtime_paths():
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text())
            public_url = str(payload.get("public_url") or "")
            validate_public_url(public_url, require_https=False)
            updated_at = float(payload.get("updated_at") or 0)
        except Exception:
            continue
        if updated_at and current_time - updated_at > RUNTIME_MAX_AGE_SECONDS:
            continue
        if require_running and not _pid_is_running(payload.get("pid")):
            continue
        return payload
    return None


def load_control_service_public_url() -> str | None:
    runtime = load_control_service_runtime()
    if runtime is None:
        return None
    return str(runtime["public_url"]).rstrip("/")


def resolve_pairing_public_url(public_url: str | None = None) -> str:
    return (
        public_url
        or os.environ.get("OMNIDOER_CONTROL_PUBLIC_URL")
        or load_control_service_public_url()
        or "http://127.0.0.1:8787"
    ).rstrip("/")

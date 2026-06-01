"""Cross-process browser relay for Control Client takeover.

The MCP sidecar owns Playwright browser objects. The Control Service runs in a
separate process, so browser frames and user input need a small file-backed
bridge under OMNIDOER_HOME.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from omnidoer.omni_policy.policy import origin_from_url
from omnidoer.paths import state_file


BROWSER_RELAY_DIR = "browser_relay"
CONTEXT_MAX_AGE_SECONDS = 120.0
FRAME_MAX_AGE_SECONDS = 30.0
PREVIEW_FRAME_INTERVAL_SECONDS = 2.0
INPUT_RESULT_MAX_AGE_SECONDS = 30.0


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)
    return cleaned or "browser"


def _context_dir(browser_context_id: str) -> Path:
    path = state_file(BROWSER_RELAY_DIR) / _safe_id(browser_context_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    tmp.replace(path)
    path.chmod(0o600)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def clear_browser_relay_context(browser_context_id: str) -> None:
    """Remove cross-process relay state for a browser context that closed cleanly."""

    try:
        shutil.rmtree(_context_dir(browser_context_id))
    except FileNotFoundError:
        pass
    except OSError:
        pass


def write_context_status(browser_context_id: str, browser_controller: object) -> dict[str, Any]:
    try:
        url = str(browser_controller.current_url())
    except Exception:
        url = ""
    try:
        origin = str(browser_controller.current_origin() or origin_from_url(url) or "")
    except Exception:
        origin = str(origin_from_url(url) or "")
    payload = {
        "browser_context_id": browser_context_id,
        "pid": os.getpid(),
        "current_url": url,
        "origin": origin,
        "updated_at": time.time(),
        "control_client_only": True,
    }
    _write_json_atomic(_context_dir(browser_context_id) / "status.json", payload)
    return payload


def write_frame(browser_context_id: str, frame: dict[str, Any]) -> None:
    payload = dict(frame)
    payload["relay_updated_at"] = time.time()
    payload.setdefault("transport", {})
    payload["transport"] = {**payload["transport"], "relay": "cross_process_file"}
    _write_json_atomic(_context_dir(browser_context_id) / "frame.json", payload)


def read_frame(browser_context_id: str, *, max_age_seconds: float = FRAME_MAX_AGE_SECONDS) -> dict[str, Any] | None:
    payload = _read_json(_context_dir(browser_context_id) / "frame.json")
    if not payload:
        return None
    updated_at = float(payload.get("relay_updated_at") or payload.get("captured_at") or 0.0)
    if time.time() - updated_at > max_age_seconds:
        return None
    return payload


def list_contexts(*, max_age_seconds: float = CONTEXT_MAX_AGE_SECONDS) -> list[dict[str, Any]]:
    root = state_file(BROWSER_RELAY_DIR)
    try:
        entries = list(root.iterdir())
    except OSError:
        return []
    contexts: list[dict[str, Any]] = []
    now = time.time()
    for entry in entries:
        if not entry.is_dir():
            continue
        payload = _read_json(entry / "status.json")
        if not payload:
            continue
        updated_at = float(payload.get("updated_at") or 0.0)
        payload["active"] = now - updated_at <= max_age_seconds
        payload["age_seconds"] = max(0.0, now - updated_at)
        if payload["active"]:
            contexts.append(payload)
    return sorted(
        contexts,
        key=lambda item: (
            -float(item.get("updated_at") or 0.0),
            str(item.get("browser_context_id") or ""),
        ),
    )


def get_context(browser_context_id: str) -> dict[str, Any] | None:
    for context in list_contexts():
        if context.get("browser_context_id") == browser_context_id:
            return context
    return None


def enqueue_input_event(browser_context_id: str, request_id: str, event: dict[str, Any]) -> dict[str, Any]:
    event_id = f"evt_{time.time_ns()}_{uuid.uuid4().hex}"
    payload = {
        "event_id": event_id,
        "request_id": request_id,
        "event": event,
        "created_at": time.time(),
        "secret_exposed_to_model": False,
    }
    path = _context_dir(browser_context_id) / "inputs" / f"{event_id}.json"
    _write_json_atomic(path, payload)
    return {"status": "event_queued", "event_id": event_id, "secret_exposed_to_model": False}


def write_input_event_result(browser_context_id: str, event_id: str, result: dict[str, Any]) -> None:
    if not event_id:
        return
    payload = {
        "event_id": event_id,
        "status": str(result.get("status") or "event_applied"),
        "request_id": str(result.get("request_id") or ""),
        "error": str(result.get("error") or "") or None,
        "applied_at": time.time(),
        "secret_exposed_to_model": False,
    }
    path = _context_dir(browser_context_id) / "input_results" / f"{_safe_id(event_id)}.json"
    _write_json_atomic(path, payload)


def read_input_event_result(
    browser_context_id: str,
    event_id: str,
    *,
    max_age_seconds: float = INPUT_RESULT_MAX_AGE_SECONDS,
    consume: bool = False,
) -> dict[str, Any] | None:
    if not event_id:
        return None
    path = _context_dir(browser_context_id) / "input_results" / f"{_safe_id(event_id)}.json"
    payload = _read_json(path)
    if not payload:
        return None
    applied_at = float(payload.get("applied_at") or 0.0)
    if time.time() - applied_at > max_age_seconds:
        try:
            path.unlink()
        except OSError:
            pass
        return None
    if consume:
        try:
            path.unlink()
        except OSError:
            pass
    return {**payload, "secret_exposed_to_model": False}


def wait_for_input_event_result(
    browser_context_id: str,
    event_id: str,
    *,
    timeout_seconds: float = 1.5,
    poll_interval_seconds: float = 0.05,
    consume: bool = True,
) -> dict[str, Any] | None:
    if not event_id:
        return None
    deadline = time.time() + max(0.0, timeout_seconds)
    while time.time() <= deadline:
        payload = read_input_event_result(browser_context_id, event_id, consume=consume)
        if payload:
            return payload
        time.sleep(max(0.01, poll_interval_seconds))
    return None


def cleanup_input_event_results(browser_context_id: str, *, max_age_seconds: float = INPUT_RESULT_MAX_AGE_SECONDS) -> None:
    results = _context_dir(browser_context_id) / "input_results"
    try:
        paths = list(results.glob("*.json"))
    except OSError:
        return
    now = time.time()
    for path in paths:
        payload = _read_json(path) or {}
        applied_at = float(payload.get("applied_at") or 0.0)
        if now - applied_at > max_age_seconds:
            try:
                path.unlink()
            except OSError:
                pass


def consume_input_events(browser_context_id: str) -> list[dict[str, Any]]:
    inputs = _context_dir(browser_context_id) / "inputs"
    try:
        paths = sorted(inputs.glob("*.json"))
    except OSError:
        return []
    events: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(path)
        try:
            path.unlink()
        except OSError:
            pass
        if payload:
            events.append(payload)
    return events


def publish_browser_relay_tick(
    browser_context_id: str,
    browser_controller: object,
    *,
    last_preview_frame_at: float = 0.0,
    force_preview_frame: bool = False,
) -> float:
    """Publish one browser status/frame/input relay tick.

    Call this from the thread that owns browser_controller when the browser
    backend is not safe to access from an auxiliary relay thread.
    """

    from omnidoer.omni_control.requests import RequestStore
    from omnidoer.omni_takeover.input_events import event_from_dict
    from omnidoer.omni_takeover.relay import apply_input_event

    store = RequestStore()
    write_context_status(browser_context_id, browser_controller)
    active_requests = [
        request
        for request in store.list()
        if request.browser_context_id == browser_context_id
        and request.request_type in {"human_takeover", "account_registration"}
        and request.status == "user_control"
    ]
    if active_requests:
        write_frame(browser_context_id, browser_controller.takeover_frame(frame_profile="balanced"))
        last_preview_frame_at = time.time()
    elif force_preview_frame or time.time() - last_preview_frame_at >= PREVIEW_FRAME_INTERVAL_SECONDS:
        write_frame(browser_context_id, browser_controller.takeover_frame(frame_profile="data_saver"))
        last_preview_frame_at = time.time()
    cleanup_input_event_results(browser_context_id)
    for payload in consume_input_events(browser_context_id):
        event_id = str(payload.get("event_id") or "")
        request_id = str(payload.get("request_id") or "")
        try:
            event = event_from_dict(payload.get("event") or {})
            result = apply_input_event(request_id, event, browser_controller=browser_controller)
            write_input_event_result(
                browser_context_id,
                event_id,
                {**result, "request_id": request_id},
            )
        except Exception as exc:
            write_input_event_result(
                browser_context_id,
                event_id,
                {"status": "event_failed", "request_id": request_id, "error": type(exc).__name__},
            )
    return last_preview_frame_at


class CrossProcessBrowserRelay:
    def __init__(self, browser_context_id: str, browser_controller: object, *, poll_interval: float = 0.75):
        self.browser_context_id = browser_context_id
        self.browser_controller = browser_controller
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"omnidoer-browser-relay-{browser_context_id}", daemon=True)

    def start(self) -> "CrossProcessBrowserRelay":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _run(self) -> None:
        last_preview_frame_at = 0.0
        while not self._stop.is_set():
            try:
                last_preview_frame_at = publish_browser_relay_tick(
                    self.browser_context_id,
                    self.browser_controller,
                    last_preview_frame_at=last_preview_frame_at,
                )
            except Exception:
                pass
            self._stop.wait(max(0.1, self.poll_interval))


def start_browser_relay(browser_context_id: str, browser_controller: object, *, poll_interval: float = 0.75) -> CrossProcessBrowserRelay:
    return CrossProcessBrowserRelay(browser_context_id, browser_controller, poll_interval=poll_interval).start()

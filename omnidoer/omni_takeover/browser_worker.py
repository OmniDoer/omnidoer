"""Thread-safe browser proxy for Control Server takeover endpoints."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any

from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_takeover.models import InputEvent


@dataclass
class _Call:
    method: str
    args: tuple
    kwargs: dict
    response: queue.Queue


class BrowserContextWorker:
    """Owns a Playwright browser on one thread and exposes safe sync calls."""

    def __init__(self, start_url: str, *, headless: bool = True):
        self.start_url = start_url
        self.headless = headless
        self._calls: queue.Queue[_Call | None] = queue.Queue()
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._relay_context_id: str | None = None
        self._relay_lock = threading.Lock()

    def start(self) -> "BrowserContextWorker":
        self._thread.start()
        self._ready.wait(timeout=20)
        if self._error is not None:
            raise self._error
        if not self._ready.is_set():
            raise TimeoutError("browser worker did not start")
        return self

    def stop(self) -> None:
        self._calls.put(None)
        self._thread.join(timeout=10)

    def __enter__(self) -> "BrowserContextWorker":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start_control_relay(self, browser_context_id: str) -> None:
        with self._relay_lock:
            self._relay_context_id = browser_context_id

    def stop_control_relay(self, browser_context_id: str | None = None) -> None:
        with self._relay_lock:
            if browser_context_id is None or self._relay_context_id == browser_context_id:
                self._relay_context_id = None

    def _control_relay_context_id(self) -> str | None:
        with self._relay_lock:
            return self._relay_context_id

    def _run(self) -> None:
        idle = object()
        last_preview_frame_at = 0.0
        try:
            with BrowserController(headless=self.headless) as browser:
                browser.open(self.start_url)
                self._ready.set()
                while True:
                    try:
                        call = self._calls.get(timeout=0.25)
                    except queue.Empty:
                        call = idle
                    if call is None:
                        break
                    if call is not idle:
                        try:
                            result = getattr(browser, call.method)(*call.args, **call.kwargs)
                            call.response.put((True, result))
                        except BaseException as exc:  # pragma: no cover - defensive relay
                            call.response.put((False, exc))
                    context_id = self._control_relay_context_id()
                    if context_id:
                        try:
                            from omnidoer.omni_takeover.cross_process import publish_browser_relay_tick

                            last_preview_frame_at = publish_browser_relay_tick(
                                context_id,
                                browser,
                                last_preview_frame_at=last_preview_frame_at,
                            )
                        except Exception:
                            pass
        except BaseException as exc:
            self._error = exc
            self._ready.set()

    def _call(self, method: str, *args, **kwargs) -> Any:
        response: queue.Queue = queue.Queue(maxsize=1)
        self._calls.put(_Call(method, args, kwargs, response))
        ok, value = response.get(timeout=20)
        if ok:
            return value
        raise value

    def takeover_frame(self, *, frame_profile: str | None = None) -> dict:
        return self._call("takeover_frame", frame_profile=frame_profile)

    def apply_user_input_event(self, event: InputEvent) -> dict:
        return self._call("apply_user_input_event", event)

    def click(self, selector: str) -> dict:
        return self._call("click", selector)

    def fill_field(self, selector: str, value: str, *, secret: bool = False) -> dict:
        return self._call("fill_field", selector, value, secret=secret)

    def detect_challenge(self) -> str | None:
        return self._call("detect_challenge")

    def detect_antibot(self) -> bool:
        return self._call("detect_antibot")

    def open(self, url: str) -> dict:
        return self._call("open", url)

    def wait_for_load_state(self) -> dict:
        return self._call("wait_for_load_state")

    def current_url(self) -> str:
        return self._call("current_url")

    def press_key(self, key: str) -> dict:
        return self._call("apply_user_input_event", InputEvent("key", key=key))

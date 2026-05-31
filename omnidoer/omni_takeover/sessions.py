"""Process-local browser context registry for Control Client takeover APIs."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


_BROWSER_CONTEXTS: dict[str, object] = {}


def register_browser_context(browser_context_id: str, browser_controller: object) -> None:
    _BROWSER_CONTEXTS[browser_context_id] = browser_controller
    start_relay = getattr(browser_controller, "start_control_relay", None)
    if callable(start_relay):
        start_relay(browser_context_id)


def unregister_browser_context(browser_context_id: str) -> None:
    browser_controller = _BROWSER_CONTEXTS.pop(browser_context_id, None)
    stop_relay = getattr(browser_controller, "stop_control_relay", None)
    if callable(stop_relay):
        stop_relay(browser_context_id)


def get_browser_context(browser_context_id: str | None) -> object | None:
    if not browser_context_id:
        return None
    return _BROWSER_CONTEXTS.get(browser_context_id)


@contextmanager
def registered_browser_context(browser_context_id: str, browser_controller: object) -> Iterator[None]:
    register_browser_context(browser_context_id, browser_controller)
    try:
        yield
    finally:
        unregister_browser_context(browser_context_id)

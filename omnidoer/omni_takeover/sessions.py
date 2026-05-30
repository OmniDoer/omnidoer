"""Process-local browser context registry for Control Client takeover APIs."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


_BROWSER_CONTEXTS: dict[str, object] = {}


def register_browser_context(browser_context_id: str, browser_controller: object) -> None:
    _BROWSER_CONTEXTS[browser_context_id] = browser_controller


def unregister_browser_context(browser_context_id: str) -> None:
    _BROWSER_CONTEXTS.pop(browser_context_id, None)


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

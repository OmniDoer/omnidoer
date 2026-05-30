"""Runtime objects owned by the OmniDoer MCP sidecar process."""

from __future__ import annotations

import atexit

from omnidoer.omni_browser.controller import BrowserController


_browser: BrowserController | None = None


def get_browser() -> BrowserController:
    global _browser
    if _browser is None:
        browser = BrowserController()
        browser.__enter__()
        _browser = browser
        atexit.register(close_browser)
    return _browser


def close_browser() -> None:
    global _browser
    if _browser is None:
        return
    browser = _browser
    _browser = None
    browser.__exit__(None, None, None)


def reset_runtime_for_tests() -> None:
    close_browser()

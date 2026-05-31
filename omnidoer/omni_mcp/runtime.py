"""Runtime objects owned by the OmniDoer MCP sidecar process."""

from __future__ import annotations

import atexit

from omnidoer.omni_browser.controller import BrowserController
from omnidoer.omni_takeover.sessions import register_browser_context, unregister_browser_context


_browser: BrowserController | None = None
_browser_relay = None


def get_browser() -> BrowserController:
    global _browser, _browser_relay
    if _browser is None:
        browser = BrowserController()
        browser.__enter__()
        _browser = browser
        register_browser_context("mcp-browser", browser)
        from omnidoer.omni_takeover.cross_process import start_browser_relay

        _browser_relay = start_browser_relay("mcp-browser", browser)
        atexit.register(close_browser)
    return _browser


def close_browser() -> None:
    global _browser, _browser_relay
    if _browser_relay is not None:
        _browser_relay.stop()
        _browser_relay = None
    if _browser is None:
        return
    browser = _browser
    _browser = None
    unregister_browser_context("mcp-browser")
    browser.__exit__(None, None, None)


def reset_runtime_for_tests() -> None:
    close_browser()

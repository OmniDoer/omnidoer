"""Runtime objects owned by the OmniDoer MCP sidecar process."""

from __future__ import annotations

import atexit

from typing import Any

from omnidoer.omni_takeover.browser_worker import BrowserContextWorker
from omnidoer.omni_takeover.sessions import register_browser_context, unregister_browser_context


_browser: BrowserContextWorker | None = None
_browser_relay_last_preview_frame_at = 0.0


def get_browser() -> BrowserContextWorker:
    global _browser
    if _browser is None:
        browser = BrowserContextWorker()
        browser.__enter__()
        _browser = browser
        register_browser_context("mcp-browser", browser)
        publish_browser_state(browser=browser)
        atexit.register(close_browser)
    return _browser


def current_browser() -> BrowserContextWorker | None:
    return _browser


def publish_browser_state(
    *,
    browser: Any | None = None,
    browser_context_id: str = "mcp-browser",
    force_preview_frame: bool = False,
) -> bool:
    """Publish MCP browser state from the browser owner thread."""

    global _browser_relay_last_preview_frame_at
    controller = browser or _browser
    if controller is None:
        return False
    try:
        from omnidoer.omni_takeover.cross_process import publish_browser_relay_tick

        _browser_relay_last_preview_frame_at = publish_browser_relay_tick(
            browser_context_id,
            controller,
            last_preview_frame_at=_browser_relay_last_preview_frame_at,
            force_preview_frame=force_preview_frame,
        )
        return True
    except Exception:
        return False


def close_browser() -> None:
    global _browser, _browser_relay_last_preview_frame_at
    if _browser is None:
        return
    browser = _browser
    _browser = None
    _browser_relay_last_preview_frame_at = 0.0
    unregister_browser_context("mcp-browser")
    browser.__exit__(None, None, None)


def reset_runtime_for_tests() -> None:
    close_browser()

"""WebSocket/SSE push contract for Cloud Direct mode.

The MVP uses HTTP/SSE-compatible event payloads and screenshot polling. This
module keeps the authorization contract explicit without introducing a third
party relay or model-facing channel.
"""

from __future__ import annotations

import json


def sse_event(event: str, payload: dict) -> bytes:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"event: {event}\ndata: {data}\n\n".encode()


def websocket_origin_allowed(origin: str | None, allowed_origin: str) -> bool:
    return bool(origin) and origin == allowed_origin

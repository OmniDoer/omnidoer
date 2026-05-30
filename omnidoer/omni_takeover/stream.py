"""Screenshot-polling stream helpers for Human Takeover."""

from __future__ import annotations

import base64
import hashlib
import json
import time


def _frame_id(data: bytes, *, url: str, origin: str, viewport_width: int, viewport_height: int) -> str:
    metadata = json.dumps(
        {
            "origin": origin,
            "url": url,
            "viewport_height": viewport_height,
            "viewport_width": viewport_width,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(data + b"\0" + metadata).hexdigest()[:24]


def current_frame() -> dict:
    return frame_from_png(
        b"omnidoer-local-takeover-frame-placeholder",
        url="about:blank",
        origin="local-placeholder",
        viewport_width=1,
        viewport_height=1,
    )


def frame_from_png(
    data: bytes,
    *,
    url: str,
    origin: str,
    viewport_width: int,
    viewport_height: int,
) -> dict:
    captured_at = time.time()
    return {
        "frame_id": _frame_id(data, url=url, origin=origin, viewport_width=viewport_width, viewport_height=viewport_height),
        "captured_at": captured_at,
        "content_type": "image/png",
        "data_b64": base64.b64encode(data).decode(),
        "url": url,
        "origin": origin,
        "viewport": {"width": viewport_width, "height": viewport_height},
        "coordinate_space": "viewport_pixels",
        "input_binding_required": True,
        "for_control_client_only": True,
        "not_for_llm": True,
    }

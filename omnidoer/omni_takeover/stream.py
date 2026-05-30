"""Screenshot-polling stream helpers for Human Takeover."""

from __future__ import annotations

import base64

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
    return {
        "content_type": "image/png",
        "data_b64": base64.b64encode(data).decode(),
        "url": url,
        "origin": origin,
        "viewport": {"width": viewport_width, "height": viewport_height},
        "for_control_client_only": True,
        "not_for_llm": True,
    }

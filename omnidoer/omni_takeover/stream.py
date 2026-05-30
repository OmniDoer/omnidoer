"""MVP screenshot-polling stream placeholder."""

from __future__ import annotations

import base64


PLACEHOLDER_PNG = base64.b64encode(
    b"omnidoer-local-takeover-frame-placeholder"
).decode()


def current_frame() -> dict:
    return {
        "content_type": "image/png",
        "data_b64": PLACEHOLDER_PNG,
        "for_control_client_only": True,
        "not_for_llm": True,
    }

"""CSRF helpers for authenticated Control Service requests."""

from __future__ import annotations

import hmac


CSRF_HEADER = "x-omnidoer-csrf"


def verify_csrf(expected_token: str, provided_token: str | None) -> bool:
    if not expected_token or not provided_token:
        return False
    return hmac.compare_digest(expected_token, provided_token)

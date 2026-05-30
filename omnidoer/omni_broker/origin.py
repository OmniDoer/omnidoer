"""Origin helpers for broker checks."""

from __future__ import annotations

from omnidoer.omni_policy.policy import origin_from_url


def exact_origin_allowed(current_url: str, allowed_origins: list[str]) -> bool:
    origin = origin_from_url(current_url)
    return origin is not None and origin in set(allowed_origins)

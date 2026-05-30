"""Initial model-visible redaction helpers.

This module is a safety fixture for the MVP. Production browser observation can
move to Rust or TypeScript, but it must preserve the same guarantees: no secret
values in model-visible observations.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


REDACTED = "[REDACTED]"

SECRET_FIELD_RE = re.compile(
    r"(password|passwd|pwd|totp|otp|mfa|2fa|token|cookie|authorization|api[-_ ]?key|"
    r"secret|private[-_ ]?key|recovery|backup[-_ ]?code|one[-_ ]?time|sms|email[-_ ]?code|"
    r"verification[-_ ]?code|passcode|challenge[-_ ]?answer|captcha[-_ ]?answer|3ds[-_ ]?code|"
    r"user[-_ ]?input|input[-_ ]?text|typed[-_ ]?text|challenge|card|cvv|cvc|iban|account)",
    re.IGNORECASE,
)

TEXT_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b(?:ghp|github_pat|sk|pk)_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?i)(password|token|api[-_ ]?key|secret|cookie)\s*[:=]\s*[^\\s<]+"),
    re.compile(
        r"(?i)\b("
        r"totp|otp|mfa|2fa|sms[-_ ]?code|email[-_ ]?code|one[-_ ]?time[-_ ]?code|"
        r"verification[-_ ]?code|captcha[-_ ]?answer|challenge[-_ ]?answer|3ds[-_ ]?code|passcode"
        r")\b\s*[:=]?\s*[A-Za-z0-9-]{4,}",
    ),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in TEXT_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def _field_is_sensitive(node: Mapping[str, Any]) -> bool:
    haystack = " ".join(
        str(node.get(key, ""))
        for key in (
            "type",
            "name",
            "id",
            "label",
            "placeholder",
            "autocomplete",
            "role",
            "aria_label",
            "description",
        )
    )
    return bool(SECRET_FIELD_RE.search(haystack))


def redact_dom_snapshot(value: Any) -> Any:
    """Redact a JSON-like DOM or accessibility snapshot."""

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [redact_dom_snapshot(item) for item in value]

    if isinstance(value, Mapping):
        sensitive = _field_is_sensitive(value)
        output: dict[str, Any] = {}
        for key, item in value.items():
            if sensitive and str(key).lower() in {"value", "text", "name", "description"}:
                output[str(key)] = REDACTED
            elif SECRET_FIELD_RE.search(str(key)):
                output[str(key)] = REDACTED
            else:
                output[str(key)] = redact_dom_snapshot(item)
        return output

    return value

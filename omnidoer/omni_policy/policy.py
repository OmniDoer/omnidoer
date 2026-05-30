"""Initial OmniDoer policy checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse


class Decision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_USER_INTERACTION = "require_user_interaction"
    REQUIRE_TAKEOVER = "require_takeover"


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason: str
    origin: str | None = None


SENSITIVE_ACTIONS = {
    "payment_submit",
    "purchase",
    "transfer",
    "subscription",
    "oauth_grant",
    "account_deletion",
    "password_change",
    "totp_change",
    "send_sensitive_message",
    "upload_sensitive_file",
}

CHALLENGE_ACTIONS = {
    "captcha",
    "totp",
    "sms",
    "email",
    "mfa",
    "passkey",
    "webauthn",
    "payment_3ds",
    "device_confirmation",
}

SENSITIVE_CLICK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "payment_submit",
        re.compile(
            r"\b(pay|purchase|buy now|place order|complete order|submit payment|checkout|subscribe|confirm payment)\b",
            re.IGNORECASE,
        ),
    ),
    ("transfer", re.compile(r"\b(send money|transfer|wire transfer|withdraw)\b", re.IGNORECASE)),
    ("oauth_grant", re.compile(r"\b(authorize|allow access|grant access|approve access)\b", re.IGNORECASE)),
    ("account_deletion", re.compile(r"\b(delete account|close account|remove account|terminate account)\b", re.IGNORECASE)),
)


def origin_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


def _is_loopback(origin: str) -> bool:
    parsed = urlparse(origin)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def _script_bucket(ch: str) -> str | None:
    code = ord(ch)
    if "a" <= ch <= "z" or "A" <= ch <= "Z":
        return "latin"
    if 0x0370 <= code <= 0x03FF:
        return "greek"
    if 0x0400 <= code <= 0x052F:
        return "cyrillic"
    return None


def suspicious_origin_reason(origin: str) -> str | None:
    parsed = urlparse(origin)
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname or _is_loopback(origin):
        return None
    labels = [label for label in hostname.split(".") if label]
    if any(label.startswith("xn--") for label in labels):
        return "punycode origin requires manual review before credential fill"
    for label in labels:
        scripts = {_script_bucket(ch) for ch in label}
        scripts.discard(None)
        if "latin" in scripts and ({"cyrillic", "greek"} & scripts):
            return "mixed-script homograph origin requires manual review before credential fill"
    return None


def evaluate_credential_fill(
    *,
    current_url: str,
    allowed_origins: set[str],
    top_level_frame: bool,
    form_action_url: str | None,
    allow_loopback_http: bool = True,
) -> PolicyDecision:
    origin = origin_from_url(current_url)
    if origin is None:
        return PolicyDecision(Decision.BLOCK, "current URL has no origin")

    suspicious = suspicious_origin_reason(origin)
    if suspicious:
        return PolicyDecision(Decision.BLOCK, suspicious, origin)

    if origin not in allowed_origins:
        return PolicyDecision(Decision.BLOCK, "origin is not allowed for credential", origin)

    if origin.startswith("http://") and not (allow_loopback_http and _is_loopback(origin)):
        return PolicyDecision(Decision.BLOCK, "HTTP credential fill is blocked", origin)

    if not top_level_frame:
        return PolicyDecision(Decision.BLOCK, "credential fill inside iframe is blocked", origin)

    if form_action_url:
        form_origin = origin_from_url(form_action_url)
        if form_origin and form_origin != origin:
            return PolicyDecision(Decision.BLOCK, "form action origin mismatch", origin)

    return PolicyDecision(Decision.ALLOW, "credential fill allowed", origin)


def requires_approval(action_type: str) -> PolicyDecision:
    if action_type in SENSITIVE_ACTIONS:
        return PolicyDecision(Decision.REQUIRE_APPROVAL, f"{action_type} requires approval")
    return PolicyDecision(Decision.ALLOW, "approval not required")


def evaluate_challenge(action_type: str) -> PolicyDecision:
    if action_type == "high_intensity_antibot":
        return PolicyDecision(Decision.REQUIRE_TAKEOVER, "high-intensity anti-bot requires human takeover")
    if action_type == "account_registration":
        return PolicyDecision(Decision.REQUIRE_TAKEOVER, "account registration requires user handoff")
    if action_type in CHALLENGE_ACTIONS:
        return PolicyDecision(Decision.REQUIRE_USER_INTERACTION, f"{action_type} requires user interaction")
    return PolicyDecision(Decision.ALLOW, "no challenge policy required")


def classify_sensitive_click(metadata: dict[str, Any]) -> str | None:
    """Classify clicks that must not proceed without human approval."""

    fields = metadata.get("form_fields") if isinstance(metadata.get("form_fields"), list) else []
    field_text = " ".join(
        " ".join(str(field.get(key, "")) for key in ("name", "id", "type", "value"))
        for field in fields
        if isinstance(field, dict)
    )
    haystack = " ".join(
        str(metadata.get(key, ""))
        for key in ("text", "value", "name", "id", "aria_label", "form_action", "current_url")
    )
    haystack = f"{haystack} {field_text}"
    for action_type, pattern in SENSITIVE_CLICK_PATTERNS:
        if pattern.search(haystack):
            return action_type
    if metadata.get("tag") == "button" and metadata.get("type") == "submit":
        lowered = haystack.lower()
        if "amount" in lowered and "currency" in lowered:
            return "payment_submit"
    return None


def policy_self_test() -> None:
    assert requires_approval("payment_submit").decision == Decision.REQUIRE_APPROVAL
    assert evaluate_challenge("captcha").decision == Decision.REQUIRE_USER_INTERACTION
    assert evaluate_challenge("high_intensity_antibot").decision == Decision.REQUIRE_TAKEOVER
    assert evaluate_challenge("account_registration").decision == Decision.REQUIRE_TAKEOVER
    assert suspicious_origin_reason("https://xn--example-9d0b.com") is not None
    assert classify_sensitive_click({"text": "Pay 12.34 USD"}) == "payment_submit"

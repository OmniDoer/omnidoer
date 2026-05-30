"""Initial OmniDoer policy checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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


def origin_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


def _is_loopback(origin: str) -> bool:
    parsed = urlparse(origin)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}


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
    if action_type in CHALLENGE_ACTIONS:
        return PolicyDecision(Decision.REQUIRE_USER_INTERACTION, f"{action_type} requires user interaction")
    return PolicyDecision(Decision.ALLOW, "no challenge policy required")


def policy_self_test() -> None:
    assert requires_approval("payment_submit").decision == Decision.REQUIRE_APPROVAL
    assert evaluate_challenge("captcha").decision == Decision.REQUIRE_USER_INTERACTION
    assert evaluate_challenge("high_intensity_antibot").decision == Decision.REQUIRE_TAKEOVER

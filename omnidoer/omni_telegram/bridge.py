"""Low-sensitivity Telegram notification bridge.

Telegram is disabled by default and is not a secret input, challenge-answer, or
human-takeover channel. This module intentionally stops at notification payload
preparation; it does not accept passwords, one-time codes, CAPTCHA answers, or
browser takeover streams.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


SENSITIVE_REQUEST_TYPES = {
    "credential",
    "totp",
    "one_time_code",
    "sms_code",
    "email_code",
    "captcha",
    "passkey",
    "webauthn",
    "device_confirmation",
    "payment_3ds",
    "human_takeover",
    "account_registration",
}


@dataclass(frozen=True)
class TelegramBridgeConfig:
    enabled: bool = False
    notify_only: bool = True


def config_from_env() -> TelegramBridgeConfig:
    return TelegramBridgeConfig(enabled=os.environ.get("OMNIDOER_TELEGRAM_ENABLED") == "1", notify_only=True)


def status() -> str:
    config = config_from_env()
    state = "enabled" if config.enabled else "disabled"
    return f"telegram bridge: {state}; notify-only; use OmniDoer Control Client for secrets, challenges, approvals, and takeover"


def notification_for_request(request: Any, *, public_url: str | None = None, config: TelegramBridgeConfig | None = None) -> dict[str, Any]:
    """Create a low-sensitivity notification payload for a pending request."""

    config = config or config_from_env()
    request_id = getattr(request, "request_id", None) or request.get("request_id")
    request_type = getattr(request, "request_type", None) or request.get("request_type")
    risk_level = getattr(request, "risk_level", None) or request.get("risk_level")
    origin = getattr(request, "origin", None) or request.get("origin")
    control_url = (public_url or "").rstrip("/") or None
    reason = "open_control_client"
    if request_type in SENSITIVE_REQUEST_TYPES:
        reason = "sensitive_request_requires_control_client"
    return {
        "enabled": config.enabled,
        "channel": "telegram",
        "notify_only": True,
        "request_id": request_id,
        "request_type": request_type,
        "origin": origin,
        "risk_level": risk_level,
        "message": "Open OmniDoer Control Client to handle the pending request.",
        "control_url": control_url,
        "reason": reason,
        "contains_secret": False,
        "contains_challenge_answer": False,
        "contains_takeover_stream": False,
    }


def reject_sensitive_input(field_name: str) -> None:
    raise PermissionError(f"Telegram is notify-only and cannot receive sensitive field: {field_name}")

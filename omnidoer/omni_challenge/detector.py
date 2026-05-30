"""Demo challenge detector."""

from __future__ import annotations


def detect_challenge_from_url(url: str) -> str | None:
    lowered = url.lower()
    if "captcha" in lowered:
        return "captcha"
    if "totp" in lowered:
        return "totp"
    if "sms" in lowered:
        return "sms"
    if "email-code" in lowered:
        return "email"
    if "3ds" in lowered:
        return "3ds"
    if "passkey" in lowered:
        return "passkey"
    return None

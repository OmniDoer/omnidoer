"""Telegram notification bridge skeleton.

Telegram is disabled by default and is not a secret input, challenge-answer, or
human-takeover channel.
"""

from __future__ import annotations


def status() -> str:
    return "telegram bridge: disabled; use OmniDoer Control Client for secrets, challenges, approvals, and takeover"

"""Pairing code helpers for future remote Control Clients."""

from __future__ import annotations

import secrets


def generate_pairing_code() -> str:
    return "-".join(secrets.token_hex(2) for _ in range(3))

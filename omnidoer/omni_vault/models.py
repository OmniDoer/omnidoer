"""Vault data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CredentialMetadata:
    credential_id: str
    username: str
    allowed_origins: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CredentialSecret:
    username: str
    password: str
    totp_seed: str | None = None

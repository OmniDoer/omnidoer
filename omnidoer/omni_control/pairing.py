"""Short-lived pairing codes for Control Clients."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from omnidoer.omni_control.secure_channel import load_or_create_keypair, load_or_create_web_keypair
from omnidoer.paths import state_file


def generate_pairing_code() -> str:
    return "-".join(secrets.token_hex(2) for _ in range(3))


def parse_duration_seconds(value: str | int | None, default: int = 600) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    text = value.strip().lower()
    if text.endswith("m"):
        return int(text[:-1]) * 60
    if text.endswith("s"):
        return int(text[:-1])
    if text.endswith("h"):
        return int(text[:-1]) * 3600
    return int(text)


@dataclass
class PairingCode:
    pairing_id: str
    code: str
    public_url: str
    broker_fingerprint: str
    web_broker_fingerprint: str
    expires_at: float
    used: bool = False
    created_at: float = field(default_factory=time.time)

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) > self.expires_at

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "pairing_id": self.pairing_id,
            "public_url": self.public_url,
            "broker_fingerprint": self.broker_fingerprint,
            "web_broker_fingerprint": self.web_broker_fingerprint,
            "expires_at": self.expires_at,
            "used": self.used,
        }


class PairingStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_pairing.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, PairingCode]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: PairingCode(**value) for key, value in raw.items()}

    def _save(self, pairings: dict[str, PairingCode]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({key: asdict(value) for key, value in pairings.items()}, indent=2, sort_keys=True))
        tmp.replace(self.path)
        self.path.chmod(0o600)

    def create(self, *, public_url: str, ttl_seconds: int = 600) -> PairingCode:
        keypair = load_or_create_keypair()
        web_keypair = load_or_create_web_keypair()
        pairing = PairingCode(
            pairing_id=f"pair_{uuid.uuid4().hex}",
            code=generate_pairing_code(),
            public_url=public_url.rstrip("/"),
            broker_fingerprint=keypair.fingerprint,
            web_broker_fingerprint=web_keypair.fingerprint,
            expires_at=time.time() + ttl_seconds,
        )
        pairings = self._load()
        pairings[pairing.pairing_id] = pairing
        self._save(pairings)
        return pairing

    def consume(self, code: str, now: float | None = None) -> PairingCode:
        pairings = self._load()
        for pairing in pairings.values():
            if pairing.code == code:
                if pairing.used:
                    raise ValueError("pairing code already used")
                if pairing.is_expired(now):
                    raise ValueError("pairing code expired")
                pairing.used = True
                pairings[pairing.pairing_id] = pairing
                self._save(pairings)
                return pairing
        raise ValueError("invalid pairing code")

    def list(self) -> list[PairingCode]:
        return sorted(self._load().values(), key=lambda item: item.created_at)


def pairing_url(pairing: PairingCode) -> str:
    return f"{pairing.public_url}/pair?code={pairing.code}&pairing_id={pairing.pairing_id}"


def qr_text(pairing: PairingCode) -> str:
    # A terminal-friendly QR placeholder. Native clients can render the URL as
    # a real QR code; this keeps the CLI dependency-free.
    return f"[QR] {pairing_url(pairing)}"

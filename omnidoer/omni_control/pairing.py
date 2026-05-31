"""Short-lived pairing codes for Control Clients."""

from __future__ import annotations

import json
import hashlib
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from io import StringIO

import qrcode

from omnidoer.omni_control.secure_channel import load_or_create_keypair, load_or_create_web_keypair
from omnidoer.paths import state_file


def generate_pairing_code() -> str:
    return "-".join(secrets.token_hex(2) for _ in range(3))


def pairing_code_hash(code: str) -> str:
    return hashlib.sha256(f"omnidoer-pairing-v1:{code}".encode("utf-8")).hexdigest()


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
    code_hash: str
    public_url: str
    broker_fingerprint: str
    web_broker_fingerprint: str
    expires_at: float
    code: str = ""
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
        pairings: dict[str, PairingCode] = {}
        for key, value in raw.items():
            if "code_hash" not in value and value.get("code"):
                value = {**value, "code_hash": pairing_code_hash(value["code"])}
            value = {**value, "code": ""}
            pairings[key] = PairingCode(**value)
        return pairings

    def _save(self, pairings: dict[str, PairingCode]) -> None:
        tmp = self.path.with_suffix(".tmp")
        payload = {}
        for key, value in pairings.items():
            item = asdict(value)
            item["code"] = ""
            payload[key] = item
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        tmp.replace(self.path)
        self.path.chmod(0o600)

    def create(self, *, public_url: str, ttl_seconds: int = 600) -> PairingCode:
        keypair = load_or_create_keypair()
        web_keypair = load_or_create_web_keypair()
        code = generate_pairing_code()
        pairing = PairingCode(
            pairing_id=f"pair_{uuid.uuid4().hex}",
            code=code,
            code_hash=pairing_code_hash(code),
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
        code_hash = pairing_code_hash(code)
        for pairing in pairings.values():
            if pairing.code_hash == code_hash:
                if pairing.used:
                    raise ValueError("pairing code already used")
                if pairing.is_expired(now):
                    raise ValueError("pairing code expired")
                pairing.used = True
                pairings[pairing.pairing_id] = pairing
                self._save(pairings)
                return pairing
        raise ValueError("invalid pairing code")

    def get(self, pairing_id: str, now: float | None = None) -> PairingCode:
        pairings = self._load()
        try:
            pairing = pairings[pairing_id]
        except KeyError as exc:
            raise KeyError(f"pairing not found: {pairing_id}") from exc
        if pairing.is_expired(now) and not pairing.used:
            pairing.used = True
            pairings[pairing.pairing_id] = pairing
            self._save(pairings)
        return pairing

    def list(self) -> list[PairingCode]:
        return sorted(self._load().values(), key=lambda item: item.created_at)


def pairing_url(pairing: PairingCode) -> str:
    return f"{pairing.public_url}/pair?code={pairing.code}&pairing_id={pairing.pairing_id}"


def qr_text(pairing: PairingCode, *, ansi: bool = False) -> str:
    return ascii_qr(pairing_url(pairing), ansi=ansi)


def ascii_qr(data: str, *, ansi: bool = False) -> str:
    """Render a real QR matrix as compact terminal-safe text.

    The pairing code is intentionally present in the QR payload, but it remains
    short-lived and one-time use. Do not log this output automatically.
    """

    qr = qrcode.QRCode(border=4)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    if len(matrix) % 2:
        matrix.append([False] * len(matrix[0]))

    buffer = StringIO()
    for top, bottom in zip(matrix[0::2], matrix[1::2]):
        row = zip(top, bottom)
        if ansi:
            render = _ansi_half_block
        else:
            render = _half_block
        cells = (render(top_cell, bottom_cell) for top_cell, bottom_cell in row)
        buffer.write("".join(cells))
        if ansi:
            buffer.write("\033[0m")
        buffer.write("\n")
    return buffer.getvalue().rstrip("\n")


def _half_block(top_dark: bool, bottom_dark: bool) -> str:
    if top_dark and bottom_dark:
        return "█"
    if top_dark:
        return "▀"
    if bottom_dark:
        return "▄"
    return " "


def _ansi_half_block(top_dark: bool, bottom_dark: bool) -> str:
    foreground = "30" if top_dark else "97"
    background = "40" if bottom_dark else "107"
    return f"\033[{foreground};{background}m▀"

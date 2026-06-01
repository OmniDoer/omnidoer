"""Device-key request signatures for Cloud Direct Control Clients."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

from omnidoer.omni_control.state_io import atomic_write_json, locked_state_file
from omnidoer.paths import state_file


DEVICE_ID_HEADER = "x-omnidoer-device-id"
DEVICE_SESSION_ID_HEADER = "x-omnidoer-session-id"
DEVICE_TS_HEADER = "x-omnidoer-device-ts"
DEVICE_NONCE_HEADER = "x-omnidoer-device-nonce"
DEVICE_SIG_HEADER = "x-omnidoer-device-sig"
DEVICE_SIGNATURE_VERSION = "omnidoer-device-v1"


def b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def device_signature_message(
    *,
    device_id: str,
    session_id: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
) -> bytes:
    return "\n".join(
        [
            DEVICE_SIGNATURE_VERSION,
            device_id,
            session_id,
            method.upper(),
            path,
            timestamp,
            nonce,
        ]
    ).encode("utf-8")


def _int_from_jwk(value: str) -> int:
    return int.from_bytes(b64url_decode(value), "big")


def load_ec_public_key(public_key: str):
    data: dict[str, Any]
    try:
        data = json.loads(public_key)
    except json.JSONDecodeError as exc:
        raise PermissionError("device public key must be a JWK") from exc
    if data.get("kty") != "EC" or data.get("crv") not in {"P-256", "prime256v1"}:
        raise PermissionError("unsupported device public key")
    numbers = ec.EllipticCurvePublicNumbers(
        x=_int_from_jwk(str(data.get("x") or "")),
        y=_int_from_jwk(str(data.get("y") or "")),
        curve=ec.SECP256R1(),
    )
    return numbers.public_key()


def verify_ecdsa_signature(*, public_key: str, signature_b64: str, message: bytes) -> None:
    verifier = load_ec_public_key(public_key)
    signature = b64url_decode(signature_b64)
    if len(signature) == 64:
        r = int.from_bytes(signature[:32], "big")
        s = int.from_bytes(signature[32:], "big")
        signature = utils.encode_dss_signature(r, s)
    try:
        verifier.verify(signature, message, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature as exc:
        raise PermissionError("device signature rejected") from exc


@dataclass
class DeviceNonce:
    key: str
    expires_at: float


class DeviceNonceStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_device_nonces.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, DeviceNonce]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: DeviceNonce(**value) for key, value in raw.items()}

    def _save(self, nonces: dict[str, DeviceNonce]) -> None:
        atomic_write_json(self.path, {key: asdict(value) for key, value in nonces.items()})

    def consume(self, *, device_id: str, nonce: str, timestamp: str, now: float | None = None, skew_seconds: int = 300) -> None:
        with locked_state_file(self.path):
            now = now or time.time()
            try:
                ts = float(timestamp)
            except ValueError as exc:
                raise PermissionError("invalid device timestamp") from exc
            if abs(now - ts) > skew_seconds:
                raise PermissionError("device signature timestamp outside allowed window")
            key = f"{device_id}:{nonce}"
            nonces = {item_key: item for item_key, item in self._load().items() if item.expires_at > now}
            if key in nonces:
                raise PermissionError("device signature nonce replayed")
            nonces[key] = DeviceNonce(key=key, expires_at=now + skew_seconds)
            self._save(nonces)

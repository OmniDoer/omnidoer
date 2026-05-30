"""Encrypted Control Client to Broker channel."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from omnidoer.paths import state_file


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def associated_data(
    request_id: str,
    origin: str,
    request_type: str,
    *,
    device_id: str | None = None,
    expires_at: float | None = None,
) -> bytes:
    data: dict[str, object] = {"request_id": request_id, "origin": origin, "request_type": request_type}
    if device_id is not None:
        data["device_id"] = device_id
    if expires_at is not None:
        data["expires_at"] = expires_at
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class BrokerKeyPair:
    private_key_b64: str
    public_key_b64: str

    @property
    def fingerprint(self) -> str:
        digest = hashlib.sha256(_unb64(self.public_key_b64)).hexdigest()
        return ":".join(digest[i : i + 2] for i in range(0, 32, 2))


@dataclass(frozen=True)
class WebBrokerKeyPair:
    private_key_pem: str
    public_jwk: dict[str, str]

    @property
    def fingerprint(self) -> str:
        raw = json.dumps(self.public_jwk, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(raw).hexdigest()
        return ":".join(digest[i : i + 2] for i in range(0, 32, 2))


def generate_keypair() -> BrokerKeyPair:
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return BrokerKeyPair(_b64(private_raw), _b64(public_raw))


def _public_numbers_to_jwk(public_numbers: ec.EllipticCurvePublicNumbers) -> dict[str, str]:
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": _b64(public_numbers.x.to_bytes(32, "big")),
        "y": _b64(public_numbers.y.to_bytes(32, "big")),
        "ext": True,
    }


def _jwk_to_public_key(jwk: dict[str, str]) -> ec.EllipticCurvePublicKey:
    numbers = ec.EllipticCurvePublicNumbers(int.from_bytes(_unb64(jwk["x"]), "big"), int.from_bytes(_unb64(jwk["y"]), "big"), ec.SECP256R1())
    return numbers.public_key()


def generate_web_keypair() -> WebBrokerKeyPair:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_jwk = _public_numbers_to_jwk(private_key.public_key().public_numbers())
    return WebBrokerKeyPair(private_pem, public_jwk)


def load_or_create_keypair(path: Path | None = None) -> BrokerKeyPair:
    path = path or state_file("broker_key.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text())
        return BrokerKeyPair(data["private_key"], data["public_key"])
    keypair = generate_keypair()
    path.write_text(json.dumps({"private_key": keypair.private_key_b64, "public_key": keypair.public_key_b64}, indent=2))
    path.chmod(0o600)
    return keypair


def load_or_create_web_keypair(path: Path | None = None) -> WebBrokerKeyPair:
    path = path or state_file("broker_web_key.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text())
        return WebBrokerKeyPair(data["private_key_pem"], data["public_jwk"])
    keypair = generate_web_keypair()
    path.write_text(json.dumps({"private_key_pem": keypair.private_key_pem, "public_jwk": keypair.public_jwk}, indent=2, sort_keys=True))
    path.chmod(0o600)
    return keypair


def _derive(shared: bytes, aad: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=hashlib.sha256(aad).digest(), info=b"omnidoer-control-v1").derive(shared)


def _derive_web(shared: bytes, aad: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=hashlib.sha256(aad).digest(), info=b"omnidoer-control-web-v1").derive(shared)


def encrypt_for_broker(
    public_key_b64: str,
    payload: dict[str, Any],
    *,
    request_id: str,
    origin: str,
    request_type: str,
    device_id: str | None = None,
    expires_at: float | None = None,
) -> dict[str, str]:
    broker_public = x25519.X25519PublicKey.from_public_bytes(_unb64(public_key_b64))
    ephemeral_private = x25519.X25519PrivateKey.generate()
    ephemeral_public = ephemeral_private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    aad = associated_data(request_id, origin, request_type, device_id=device_id, expires_at=expires_at)
    key = _derive(ephemeral_private.exchange(broker_public), aad)
    nonce = os.urandom(12)
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    envelope = {
        "version": "v1",
        "ephemeral_public_key": _b64(ephemeral_public),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "request_id": request_id,
        "origin": origin,
        "request_type": request_type,
    }
    if device_id is not None:
        envelope["device_id"] = device_id
    if expires_at is not None:
        envelope["expires_at"] = str(expires_at)
    return envelope


def encrypt_for_broker_web(
    public_jwk: dict[str, str],
    payload: dict[str, Any],
    *,
    request_id: str,
    origin: str,
    request_type: str,
    device_id: str | None = None,
    expires_at: float | None = None,
) -> dict[str, Any]:
    broker_public = _jwk_to_public_key(public_jwk)
    ephemeral_private = ec.generate_private_key(ec.SECP256R1())
    ephemeral_public_jwk = _public_numbers_to_jwk(ephemeral_private.public_key().public_numbers())
    aad = associated_data(request_id, origin, request_type, device_id=device_id, expires_at=expires_at)
    key = _derive_web(ephemeral_private.exchange(ec.ECDH(), broker_public), aad)
    nonce = os.urandom(12)
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    envelope = {
        "version": "web-p256-v1",
        "ephemeral_public_jwk": ephemeral_public_jwk,
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "request_id": request_id,
        "origin": origin,
        "request_type": request_type,
    }
    if device_id is not None:
        envelope["device_id"] = device_id
    if expires_at is not None:
        envelope["expires_at"] = expires_at
    return envelope


class ReplayGuard:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("secure_channel_replay.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def check_and_mark(self, envelope: dict[str, str]) -> None:
        marker = hashlib.sha256(
            f"{envelope.get('request_id')}:{envelope.get('nonce')}:{envelope.get('ciphertext')}".encode()
        ).hexdigest()
        seen: set[str] = set()
        if self.path.exists():
            seen = set(json.loads(self.path.read_text()))
        if marker in seen:
            raise ValueError("replay detected")
        seen.add(marker)
        self.path.write_text(json.dumps(sorted(seen), indent=2))


def decrypt_at_broker(
    private_key_b64: str,
    envelope: dict[str, str],
    *,
    request_id: str,
    origin: str,
    request_type: str,
    device_id: str | None = None,
    expires_at: float | None = None,
    replay_guard: ReplayGuard | None = None,
) -> dict[str, Any]:
    if envelope.get("request_id") != request_id or envelope.get("origin") != origin or envelope.get("request_type") != request_type:
        raise ValueError("envelope associated data mismatch")
    if device_id is not None and envelope.get("device_id") != device_id:
        raise ValueError("envelope associated data mismatch")
    if expires_at is not None and float(envelope.get("expires_at", "nan")) != float(expires_at):
        raise ValueError("envelope associated data mismatch")
    aad_device_id = device_id if device_id is not None else envelope.get("device_id")
    aad_expires_at = expires_at if expires_at is not None else (float(envelope["expires_at"]) if envelope.get("expires_at") is not None else None)
    if replay_guard:
        replay_guard.check_and_mark(envelope)
    private_key = x25519.X25519PrivateKey.from_private_bytes(_unb64(private_key_b64))
    ephemeral_public = x25519.X25519PublicKey.from_public_bytes(_unb64(envelope["ephemeral_public_key"]))
    aad = associated_data(request_id, origin, request_type, device_id=aad_device_id, expires_at=aad_expires_at)
    key = _derive(private_key.exchange(ephemeral_public), aad)
    plaintext = AESGCM(key).decrypt(_unb64(envelope["nonce"]), _unb64(envelope["ciphertext"]), aad)
    return json.loads(plaintext.decode())


def decrypt_web_at_broker(
    private_key_pem: str,
    envelope: dict[str, Any],
    *,
    request_id: str,
    origin: str,
    request_type: str,
    device_id: str | None = None,
    expires_at: float | None = None,
    replay_guard: ReplayGuard | None = None,
) -> dict[str, Any]:
    if envelope.get("request_id") != request_id or envelope.get("origin") != origin or envelope.get("request_type") != request_type:
        raise ValueError("envelope associated data mismatch")
    if device_id is not None and envelope.get("device_id") != device_id:
        raise ValueError("envelope associated data mismatch")
    if expires_at is not None and float(envelope.get("expires_at", "nan")) != float(expires_at):
        raise ValueError("envelope associated data mismatch")
    aad_device_id = device_id if device_id is not None else envelope.get("device_id")
    aad_expires_at = expires_at if expires_at is not None else (float(envelope["expires_at"]) if envelope.get("expires_at") is not None else None)
    if replay_guard:
        replay_guard.check_and_mark(envelope)
    private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("not an EC private key")
    ephemeral_public = _jwk_to_public_key(envelope["ephemeral_public_jwk"])
    aad = associated_data(request_id, origin, request_type, device_id=aad_device_id, expires_at=aad_expires_at)
    key = _derive_web(private_key.exchange(ec.ECDH(), ephemeral_public), aad)
    plaintext = AESGCM(key).decrypt(_unb64(envelope["nonce"]), _unb64(envelope["ciphertext"]), aad)
    return json.loads(plaintext.decode())


def decrypt_control_envelope(
    envelope: dict[str, Any],
    *,
    request_id: str,
    origin: str,
    request_type: str,
    device_id: str | None = None,
    expires_at: float | None = None,
    replay_guard: ReplayGuard | None = None,
) -> dict[str, Any]:
    if envelope.get("version") == "web-p256-v1":
        return decrypt_web_at_broker(
            load_or_create_web_keypair().private_key_pem,
            envelope,
            request_id=request_id,
            origin=origin,
            request_type=request_type,
            device_id=device_id,
            expires_at=expires_at,
            replay_guard=replay_guard,
        )
    return decrypt_at_broker(
        load_or_create_keypair().private_key_b64,
        envelope,
        request_id=request_id,
        origin=origin,
        request_type=request_type,
        device_id=device_id,
        expires_at=expires_at,
        replay_guard=replay_guard,
    )

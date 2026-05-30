"""Vault crypto primitives."""

from __future__ import annotations

import base64
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def random_b64(length: int) -> str:
    return b64(os.urandom(length))


def derive_key(passphrase: str, salt_b64: str) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode(),
        salt=unb64(salt_b64),
        time_cost=3,
        memory_cost=64 * 1024,
        parallelism=1,
        hash_len=32,
        type=Type.ID,
    )


def encrypt_json_bytes(key: bytes, plaintext: bytes, aad: bytes) -> tuple[str, str]:
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return b64(nonce), b64(ciphertext)


def decrypt_json_bytes(key: bytes, nonce_b64: str, ciphertext_b64: str, aad: bytes) -> bytes:
    return AESGCM(key).decrypt(unb64(nonce_b64), unb64(ciphertext_b64), aad)

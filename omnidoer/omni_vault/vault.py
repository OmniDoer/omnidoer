"""Encrypted Vault implementation and CLI handlers."""

from __future__ import annotations

import getpass
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from omnidoer.omni_observer.redactor import redact_dom_snapshot
from omnidoer.omni_vault.crypto import decrypt_json_bytes, derive_key, encrypt_json_bytes, random_b64
from omnidoer.omni_vault.models import CredentialMetadata, CredentialSecret


VAULT_VERSION = 1


def username_hint(username: str) -> str:
    text = username.strip()
    if not text:
        return ""
    if "@" in text:
        local, domain = text.split("@", 1)
        local_hint = f"{local[:1]}***" if local else "***"
        return f"{local_hint}@{domain}"
    if len(text) <= 2:
        return "***"
    return f"{text[:1]}***{text[-1:]}"


def _passphrase_from_env(name: str | None) -> str:
    if name:
        value = os.environ.get(name)
        if value is None:
            raise SystemExit(f"passphrase environment variable is not set: {name}")
        return value
    return getpass.getpass("Vault passphrase: ")


class Vault:
    def __init__(self, path: Path, data: dict[str, Any], key: bytes | None = None):
        self.path = path
        self.data = data
        self.key = key

    @classmethod
    def create(cls, path: str | Path, passphrase: str) -> "Vault":
        vault_path = Path(path)
        vault_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": VAULT_VERSION,
            "kdf": "argon2id",
            "salt": random_b64(16),
            "created_at": time.time(),
            "credentials": [],
        }
        vault = cls(vault_path, data, derive_key(passphrase, data["salt"]))
        vault.save()
        vault_path.chmod(0o600)
        return vault

    @classmethod
    def load(cls, path: str | Path, passphrase: str | None = None) -> "Vault":
        vault_path = Path(path)
        data = json.loads(vault_path.read_text())
        key = derive_key(passphrase, data["salt"]) if passphrase is not None else None
        return cls(vault_path, data, key)

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True))
        tmp.replace(self.path)
        self.path.chmod(0o600)

    def list_metadata(self) -> list[CredentialMetadata]:
        return [
            CredentialMetadata(
                credential_id=item["credential_id"],
                username=item.get("username_hint") or username_hint(item.get("username", "")),
                allowed_origins=list(item.get("allowed_origins", [])),
                metadata=dict(item.get("metadata", {})),
            )
            for item in self.data.get("credentials", [])
        ]

    def add_credential(
        self,
        *,
        username: str,
        password: str,
        allowed_origins: list[str],
        totp_seed: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if self.key is None:
            raise ValueError("vault is locked")
        credential_id = f"cred_{uuid.uuid4().hex}"
        secret = {"username": username, "password": password, "totp_seed": totp_seed or ""}
        aad = credential_id.encode()
        nonce, ciphertext = encrypt_json_bytes(self.key, json.dumps(secret, sort_keys=True).encode(), aad)
        self.data.setdefault("credentials", []).append(
            {
                "credential_id": credential_id,
                "username_hint": username_hint(username),
                "allowed_origins": sorted(set(allowed_origins)),
                "metadata": redact_dom_snapshot(metadata or {}),
                "secret_nonce": nonce,
                "secret_ciphertext": ciphertext,
                "created_at": time.time(),
            }
        )
        self.save()
        return credential_id

    def find_for_origin(self, origin: str) -> list[CredentialMetadata]:
        return [cred for cred in self.list_metadata() if origin in cred.allowed_origins]

    def decrypt_credential(self, credential_id: str) -> CredentialSecret:
        if self.key is None:
            raise ValueError("vault is locked")
        for item in self.data.get("credentials", []):
            if item["credential_id"] == credential_id:
                raw = decrypt_json_bytes(
                    self.key,
                    item["secret_nonce"],
                    item["secret_ciphertext"],
                    item["credential_id"].encode(),
                )
                data = json.loads(raw.decode())
                return CredentialSecret(username=data["username"], password=data["password"], totp_seed=data.get("totp_seed") or None)
        raise KeyError(f"credential not found: {credential_id}")


def handle_vault_command(args) -> int:
    if args.vault_command == "create":
        passphrase = _passphrase_from_env(args.passphrase_env)
        Vault.create(args.path, passphrase)
        print(f"vault created at {args.path}")
        return 0
    if args.vault_command == "unlock":
        passphrase = _passphrase_from_env(args.passphrase_env)
        Vault.load(args.path, passphrase)
        print(f"vault unlocked: {args.path}")
        return 0
    return 0

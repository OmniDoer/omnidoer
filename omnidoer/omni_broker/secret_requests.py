"""Credential request and CLI helpers."""

from __future__ import annotations

import getpass
import json
import os
import time
from pathlib import Path

from omnidoer.omni_broker.broker import SecretBroker
from omnidoer.omni_control.pairing import parse_duration_seconds
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, load_or_create_keypair
from omnidoer.omni_vault.vault import Vault, _passphrase_from_source


ABORTED_REQUEST_STATUSES = {"denied", "expired", "cancelled", "rejected", "failed"}


def _wait_for_encrypted_response(request_id: str, *, timeout_seconds: int) -> None:
    store = RequestStore()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = store.get(request_id)
        if request.response_ciphertext:
            return
        if request.status in ABORTED_REQUEST_STATUSES:
            raise RuntimeError(f"credential request ended: {request.status}")
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for Control Client credential response")


def _ensure_vault_for_save(path: str, passphrase: str, *, create_vault: bool) -> None:
    vault_path = Path(path)
    if vault_path.exists():
        Vault.load(vault_path, passphrase)
        return
    if not create_vault:
        raise FileNotFoundError(f"vault not found: {vault_path}")
    Vault.create(vault_path, passphrase)


def _credential_requested_fields(args) -> list[str]:
    fields = ["username", "password"]
    if not args.no_totp_field:
        fields.append("totp_seed")
    return fields


def _credential_structured_details(args) -> dict:
    labels = {
        "username": args.username_label or "Username",
        "password": args.password_label or "Password",
        "totp_seed": args.totp_label or "TOTP seed",
    }
    return {"credential_labels": labels}


def handle_cred_command(args) -> int:
    if args.cred_command == "add":
        passphrase = _passphrase_from_source(args.passphrase_env, getattr(args, "passphrase_file", None))
        vault = Vault.load(args.vault, passphrase)
        if os.environ.get("OMNIDOER_CONTROL_TEST_MODE") == "1":
            password = os.environ.get("OMNIDOER_TEST_PASSWORD", "")
            totp_seed = os.environ.get("OMNIDOER_TEST_TOTP_SECRET", "")
        else:
            password = getpass.getpass("Password: ")
            totp_seed = getpass.getpass("TOTP seed (optional): ")
        credential_id = vault.add_credential(
            username=args.username,
            password=password,
            totp_seed=totp_seed or None,
            allowed_origins=[args.origin],
        )
        print(f"credential added: {credential_id}")
        return 0
    if args.cred_command == "request":
        keypair = load_or_create_keypair()
        origin = args.origin.rstrip("/")
        request = RequestStore().create(
            "credential",
            origin=origin,
            top_level_url=args.top_level_url or origin,
            action_summary=args.summary,
            risk_level=args.risk_level,
            ttl_seconds=parse_duration_seconds(args.ttl),
            broker_public_key_fingerprint=keypair.fingerprint,
            requested_fields=_credential_requested_fields(args),
            save_to_vault=not args.no_save_to_vault,
            structured_details=_credential_structured_details(args),
        )
        print(f"credential_request={request.request_id}", flush=True)
        print(f"origin={request.origin}", flush=True)
        print(f"expires_at={request.expires_at}", flush=True)
        print("secret_exposed_to_model=false", flush=True)
        print("open the OmniDoer Control Client to submit this credential", flush=True)
        if args.wait:
            timeout_seconds = parse_duration_seconds(args.wait_timeout, parse_duration_seconds(args.ttl))
            print("waiting_for_control_client=true", flush=True)
            _wait_for_encrypted_response(request.request_id, timeout_seconds=timeout_seconds)
            if request.save_to_vault:
                passphrase = _passphrase_from_source(args.passphrase_env, getattr(args, "passphrase_file", None))
                _ensure_vault_for_save(args.vault, passphrase, create_vault=args.create_vault)
                broker = SecretBroker(
                    vault_path=args.vault,
                    vault_passphrase=passphrase,
                    replay_guard=ReplayGuard(),
                )
            else:
                broker = SecretBroker(replay_guard=ReplayGuard())
            result = broker.store_or_use_once(request.request_id)
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.cred_command == "save-request":
        if args.wait:
            timeout_seconds = parse_duration_seconds(args.wait_timeout)
            print("waiting_for_control_client=true", flush=True)
            _wait_for_encrypted_response(args.request_id, timeout_seconds=timeout_seconds)
        passphrase = _passphrase_from_source(args.passphrase_env, getattr(args, "passphrase_file", None))
        _ensure_vault_for_save(args.vault, passphrase, create_vault=args.create_vault)
        broker = SecretBroker(
            vault_path=args.vault,
            vault_passphrase=passphrase,
            replay_guard=ReplayGuard(),
        )
        result = broker.store_or_use_once(args.request_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.cred_command == "list":
        vault = Vault.load(args.vault)
        print(json.dumps([cred.__dict__ for cred in vault.list_metadata()], indent=2, sort_keys=True))
        return 0
    return 0

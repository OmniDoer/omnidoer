"""Credential request and CLI helpers."""

from __future__ import annotations

import getpass
import json
import os

from omnidoer.omni_broker.broker import SecretBroker
from omnidoer.omni_control.pairing import parse_duration_seconds
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, load_or_create_keypair
from omnidoer.omni_vault.vault import Vault, _passphrase_from_env


def handle_cred_command(args) -> int:
    if args.cred_command == "add":
        passphrase = _passphrase_from_env(args.passphrase_env)
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
            requested_fields=["username", "password", "totp_seed"],
            save_to_vault=not args.no_save_to_vault,
        )
        print(f"credential_request={request.request_id}")
        print(f"origin={request.origin}")
        print(f"expires_at={request.expires_at}")
        print("secret_exposed_to_model=false")
        print("open the OmniDoer Control Client to submit this credential")
        return 0
    if args.cred_command == "save-request":
        passphrase = _passphrase_from_env(args.passphrase_env)
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

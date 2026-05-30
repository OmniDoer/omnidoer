"""Credential request and CLI helpers."""

from __future__ import annotations

import getpass
import json
import os

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
    if args.cred_command == "list":
        vault = Vault.load(args.vault)
        print(json.dumps([cred.__dict__ for cred in vault.list_metadata()], indent=2, sort_keys=True))
        return 0
    return 0

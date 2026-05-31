"""Vault-backed Git HTTPS credential bridge."""

from __future__ import annotations

import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from omnidoer.omni_policy.policy import origin_from_url, suspicious_origin_reason
from omnidoer.omni_vault.models import CredentialMetadata, CredentialSecret
from omnidoer.omni_vault.vault import Vault, _passphrase_from_env


PROMPT_URL_RE = re.compile(r"['\"](https?://[^'\"]+)['\"]")


def normalize_git_origin(origin: str) -> str:
    normalized = origin_from_url(origin)
    if normalized is None:
        raise ValueError("git credential origin must include scheme and host")
    if not normalized.startswith("https://"):
        raise PermissionError("git credential origin must use HTTPS")
    suspicious = suspicious_origin_reason(normalized)
    if suspicious:
        raise PermissionError(suspicious)
    return normalized


def prompt_origin(prompt: str) -> str | None:
    match = PROMPT_URL_RE.search(prompt)
    if not match:
        return None
    return origin_from_url(match.group(1))


def _metadata_for_origin(vault: Vault, origin: str, credential_id: str | None) -> CredentialMetadata:
    metadata = vault.list_metadata()
    if credential_id:
        match = next((item for item in metadata if item.credential_id == credential_id), None)
        if match is None:
            raise KeyError("credential not found")
        if origin not in match.allowed_origins:
            raise PermissionError("credential is not allowed for git origin")
        return match
    matches = [item for item in metadata if origin in item.allowed_origins]
    if not matches:
        raise KeyError("no credential for git origin")
    return matches[0]


def load_git_credential(
    *,
    origin: str,
    vault_path: str | Path,
    passphrase_env: str | None,
    credential_id: str | None = None,
) -> tuple[CredentialMetadata, CredentialSecret]:
    normalized = normalize_git_origin(origin)
    vault = Vault.load(vault_path, _passphrase_from_env(passphrase_env))
    metadata = _metadata_for_origin(vault, normalized, credential_id)
    return metadata, vault.decrypt_credential(metadata.credential_id)


def askpass_response(
    prompt: str,
    *,
    origin: str,
    vault_path: str | Path,
    passphrase_env: str | None,
    credential_id: str | None = None,
) -> str:
    normalized = normalize_git_origin(origin)
    seen_origin = prompt_origin(prompt)
    if seen_origin is not None and seen_origin != normalized:
        raise PermissionError("git credential prompt origin mismatch")
    _metadata, secret = load_git_credential(
        origin=normalized,
        vault_path=vault_path,
        passphrase_env=passphrase_env,
        credential_id=credential_id,
    )
    lowered = prompt.lower()
    if "username" in lowered:
        return secret.username
    if "password" in lowered or "token" in lowered:
        return secret.password
    return ""


def _askpass_grant_valid() -> bool:
    token = os.environ.get("OMNIDOER_GIT_ASKPASS_TOKEN")
    token_file = os.environ.get("OMNIDOER_GIT_ASKPASS_TOKEN_FILE")
    if not token or not token_file:
        return False
    try:
        return Path(token_file).read_text().strip() == token
    except OSError:
        return False


def _helper_script() -> str:
    return f"""#!/bin/sh
exec {sys.executable!r} -m omnidoer.omni_cli.main git _askpass "$@"
"""


def _git_args(raw: list[str]) -> list[str]:
    args = list(raw)
    if args[:1] == ["--"]:
        args = args[1:]
    if args[:1] == ["git"]:
        args = args[1:]
    if not args:
        raise ValueError("git arguments are required")
    return args


def handle_git_command(args) -> int:
    if args.git_command == "_askpass":
        if not _askpass_grant_valid():
            print("OmniDoer git askpass grant missing", file=sys.stderr)
            return 2
        try:
            response = askpass_response(
                args.prompt or "",
                origin=os.environ.get("OMNIDOER_GIT_ORIGIN", ""),
                vault_path=os.environ.get("OMNIDOER_GIT_VAULT", ".omnidoer/vault.json"),
                passphrase_env=os.environ.get("OMNIDOER_GIT_PASSPHRASE_ENV") or None,
                credential_id=os.environ.get("OMNIDOER_GIT_CREDENTIAL_ID") or None,
            )
        except Exception as exc:
            print(f"OmniDoer git askpass denied: {type(exc).__name__}", file=sys.stderr)
            return 1
        print(response)
        return 0

    if args.git_command == "run":
        try:
            git_args = _git_args(args.git_args)
            normalized = normalize_git_origin(args.origin)
            metadata, _secret = load_git_credential(
                origin=normalized,
                vault_path=args.vault,
                passphrase_env=args.passphrase_env,
                credential_id=args.credential_id,
            )
        except Exception as exc:
            print(f"OmniDoer git credential unavailable: {type(exc).__name__}", file=sys.stderr)
            return 2

        with tempfile.TemporaryDirectory(prefix="omnidoer-git-") as tmp:
            tmp_path = Path(tmp)
            helper = tmp_path / "askpass.sh"
            token_file = tmp_path / "grant"
            token = secrets.token_urlsafe(32)
            helper.write_text(_helper_script())
            helper.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            token_file.write_text(token)
            token_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

            env = os.environ.copy()
            env.update(
                {
                    "GIT_ASKPASS": str(helper),
                    "GIT_TERMINAL_PROMPT": "0",
                    "OMNIDOER_GIT_ASKPASS_TOKEN": token,
                    "OMNIDOER_GIT_ASKPASS_TOKEN_FILE": str(token_file),
                    "OMNIDOER_GIT_ORIGIN": normalized,
                    "OMNIDOER_GIT_VAULT": str(args.vault),
                    "OMNIDOER_GIT_PASSPHRASE_ENV": args.passphrase_env or "",
                    "OMNIDOER_GIT_CREDENTIAL_ID": metadata.credential_id,
                }
            )
            git_bin = os.environ.get("OMNIDOER_GIT_BIN", "git")
            result = subprocess.run([git_bin, *git_args], env=env, check=False)
            return int(result.returncode)

    return 0

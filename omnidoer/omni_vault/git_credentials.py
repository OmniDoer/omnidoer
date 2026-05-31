"""Vault-backed Git HTTPS credential bridge."""

from __future__ import annotations

import os
import re
import secrets
import socket
import stat
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from omnidoer.omni_policy.policy import origin_from_url, suspicious_origin_reason
from omnidoer.omni_vault.models import CredentialMetadata, CredentialSecret
from omnidoer.omni_vault.vault import Vault, _passphrase_from_source


PROMPT_URL_RE = re.compile(r"['\"](https?://[^'\"]+)['\"]")
GIT_ENV_ALLOWLIST = {
    "HOME",
    "PATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TZ",
    "SSH_AUTH_SOCK",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "GIT_SSL_CAINFO",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_TRACE",
    "GIT_TRACE_PACKET",
    "GIT_CURL_VERBOSE",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
}


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
    passphrase_file: str | Path | None = None,
    credential_id: str | None = None,
) -> tuple[CredentialMetadata, CredentialSecret]:
    normalized = normalize_git_origin(origin)
    vault = Vault.load(vault_path, _passphrase_from_source(passphrase_env, passphrase_file))
    metadata = _metadata_for_origin(vault, normalized, credential_id)
    return metadata, vault.decrypt_credential(metadata.credential_id)


def askpass_response(
    prompt: str,
    *,
    origin: str,
    secret: CredentialSecret | None = None,
    vault_path: str | Path | None = None,
    passphrase_env: str | None = None,
    passphrase_file: str | Path | None = None,
    credential_id: str | None = None,
) -> str:
    normalized = normalize_git_origin(origin)
    seen_origin = prompt_origin(prompt)
    if seen_origin is not None and seen_origin != normalized:
        raise PermissionError("git credential prompt origin mismatch")
    if secret is None:
        if vault_path is None:
            raise ValueError("vault path is required")
        _metadata, secret = load_git_credential(
            origin=normalized,
            vault_path=vault_path,
            passphrase_env=passphrase_env,
            passphrase_file=passphrase_file,
            credential_id=credential_id,
        )
    lowered = prompt.lower()
    if "username" in lowered:
        return secret.username
    if "password" in lowered or "token" in lowered:
        return secret.password
    return ""


def _askpass_grant_valid() -> bool:
    return bool(os.environ.get("OMNIDOER_GIT_ASKPASS_SOCKET") and os.environ.get("OMNIDOER_GIT_ASKPASS_TOKEN"))


def _askpass_broker_response(prompt: str) -> str:
    import json

    socket_path = os.environ.get("OMNIDOER_GIT_ASKPASS_SOCKET")
    token = os.environ.get("OMNIDOER_GIT_ASKPASS_TOKEN")
    if not socket_path or not token:
        raise PermissionError("askpass broker unavailable")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(socket_path)
        client.sendall(json.dumps({"token": token, "prompt": prompt}).encode() + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
    payload = json.loads(data.decode() or "{}")
    if payload.get("status") != "ok":
        raise PermissionError(str(payload.get("error") or "askpass denied"))
    return str(payload.get("response") or "")


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


class AskpassBroker:
    def __init__(self, *, socket_path: Path, token: str, origin: str, secret: CredentialSecret):
        self.socket_path = socket_path
        self.token = token
        self.origin = origin
        self.secret = secret
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self) -> "AskpassBroker":
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise TimeoutError("askpass broker did not start")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._stop.set()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.2)
                client.connect(str(self.socket_path))
                client.sendall(b"{}\n")
        except OSError:
            pass
        self._thread.join(timeout=2)
        try:
            self.socket_path.unlink()
        except OSError:
            pass

    def _serve(self) -> None:
        import json

        try:
            self.socket_path.unlink()
        except OSError:
            pass
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(self.socket_path))
            self.socket_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            server.listen(8)
            server.settimeout(0.2)
            self._ready.set()
            while not self._stop.is_set():
                try:
                    conn, _addr = server.accept()
                except TimeoutError:
                    continue
                except OSError:
                    break
                with conn:
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                    try:
                        request = json.loads(data.decode() or "{}")
                        if request.get("token") != self.token:
                            raise PermissionError("invalid askpass token")
                        response = askpass_response(str(request.get("prompt") or ""), origin=self.origin, secret=self.secret)
                        payload = {"status": "ok", "response": response}
                    except Exception as exc:
                        payload = {"status": "denied", "error": type(exc).__name__}
                    try:
                        conn.sendall(json.dumps(payload).encode() + b"\n")
                    except BrokenPipeError:
                        pass


def _git_env(base: dict[str, str], *, helper: Path, socket_path: Path, token: str, origin: str) -> dict[str, str]:
    env = {key: value for key, value in base.items() if key in GIT_ENV_ALLOWLIST or key.startswith("LC_")}
    env.update(
        {
            "GIT_ASKPASS": str(helper),
            "GIT_TERMINAL_PROMPT": "0",
            "OMNIDOER_GIT_ASKPASS_SOCKET": str(socket_path),
            "OMNIDOER_GIT_ASKPASS_TOKEN": token,
            "OMNIDOER_GIT_ORIGIN": origin,
        }
    )
    return env


def handle_git_command(args) -> int:
    if args.git_command == "_askpass":
        if not _askpass_grant_valid():
            print("OmniDoer git askpass grant missing", file=sys.stderr)
            return 2
        try:
            response = _askpass_broker_response(args.prompt or "")
        except Exception as exc:
            print(f"OmniDoer git askpass denied: {type(exc).__name__}", file=sys.stderr)
            return 1
        print(response)
        return 0

    if args.git_command == "run":
        try:
            git_args = _git_args(args.git_args)
            normalized = normalize_git_origin(args.origin)
            _metadata, secret = load_git_credential(
                origin=normalized,
                vault_path=args.vault,
                passphrase_env=args.passphrase_env,
                passphrase_file=args.passphrase_file,
                credential_id=args.credential_id,
            )
        except Exception as exc:
            print(f"OmniDoer git credential unavailable: {type(exc).__name__}", file=sys.stderr)
            return 2

        with tempfile.TemporaryDirectory(prefix="omnidoer-git-") as tmp:
            tmp_path = Path(tmp)
            helper = tmp_path / "askpass.sh"
            socket_path = tmp_path / "askpass.sock"
            token = secrets.token_urlsafe(32)
            helper.write_text(_helper_script())
            helper.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

            env = _git_env(os.environ, helper=helper, socket_path=socket_path, token=token, origin=normalized)
            git_bin = os.environ.get("OMNIDOER_GIT_BIN", "git")
            with AskpassBroker(socket_path=socket_path, token=token, origin=normalized, secret=secret):
                result = subprocess.run([git_bin, *git_args], env=env, check=False)
            return int(result.returncode)

    return 0

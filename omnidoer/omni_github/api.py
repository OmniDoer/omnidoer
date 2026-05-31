"""Vault-backed GitHub API client."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from omnidoer.omni_observer.redactor import redact_text
from omnidoer.omni_policy.policy import origin_from_url, suspicious_origin_reason
from omnidoer.omni_vault.git_credentials import load_git_credential, normalize_git_origin
from omnidoer.omni_vault.models import CredentialSecret


DEFAULT_GITHUB_API_ORIGIN = "https://api.github.com"
ALLOWED_METHODS = {"GET", "POST", "PATCH", "PUT", "DELETE"}


@dataclass(frozen=True)
class GitHubApiResult:
    status_code: int
    body: str
    secret_exposed_to_model: bool = False


def normalize_api_origin(api_origin: str, *, insecure_dev_api: bool = False) -> str:
    origin = origin_from_url(api_origin)
    if origin is None:
        raise ValueError("GitHub API origin must include scheme and host")
    parsed = urlparse(origin)
    if parsed.scheme != "https" and not insecure_dev_api:
        raise PermissionError("GitHub API origin must use HTTPS")
    if parsed.hostname != "api.github.com" and not insecure_dev_api:
        raise PermissionError("GitHub API origin must be api.github.com")
    suspicious = suspicious_origin_reason(origin)
    if suspicious:
        raise PermissionError(suspicious)
    return origin


def normalize_api_path(path: str) -> str:
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("GitHub API path must be an absolute path like /repos/owner/repo")
    if "://" in path:
        raise ValueError("GitHub API path must not be a full URL")
    return path


def _body_bytes(body_json: str | None) -> bytes | None:
    if body_json is None:
        return None
    parsed = json.loads(body_json)
    return json.dumps(parsed, separators=(",", ":"), sort_keys=True).encode()


def redact_api_output(text: str, *, secret: CredentialSecret) -> str:
    redacted = text.replace(secret.password, "[REDACTED]") if secret.password else text
    return redact_text(redacted)


def github_api_request(
    *,
    method: str,
    path: str,
    api_origin: str,
    origin: str,
    vault_path: str,
    passphrase_env: str | None,
    credential_id: str | None = None,
    body_json: str | None = None,
    insecure_dev_api: bool = False,
    timeout_seconds: int = 30,
) -> GitHubApiResult:
    normalized_method = method.upper()
    if normalized_method not in ALLOWED_METHODS:
        raise ValueError("unsupported GitHub API method")
    normalized_origin = normalize_git_origin(origin)
    normalized_api_origin = normalize_api_origin(api_origin, insecure_dev_api=insecure_dev_api)
    api_path = normalize_api_path(path)
    _metadata, secret = load_git_credential(
        origin=normalized_origin,
        vault_path=vault_path,
        passphrase_env=passphrase_env,
        credential_id=credential_id,
    )
    body = _body_bytes(body_json)
    headers = {
        "accept": "application/vnd.github+json",
        "authorization": f"Bearer {secret.password}",
        "user-agent": "OmniDoer",
        "x-github-api-version": "2022-11-28",
    }
    if body is not None:
        headers["content-type"] = "application/json"
    request = Request(f"{normalized_api_origin}{api_path}", data=body, headers=headers, method=normalized_method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", "replace")
            return GitHubApiResult(response.status, redact_api_output(raw, secret=secret))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        return GitHubApiResult(exc.code, redact_api_output(raw, secret=secret))


def handle_github_command(args) -> int:
    if args.github_command != "api":
        return 0
    try:
        result = github_api_request(
            method=args.method,
            path=args.path,
            api_origin=args.api_origin,
            origin=args.origin,
            vault_path=args.vault,
            passphrase_env=args.passphrase_env,
            credential_id=args.credential_id,
            body_json=args.body_json,
            insecure_dev_api=args.insecure_dev_api,
        )
    except Exception as exc:
        print(f"OmniDoer GitHub API unavailable: {type(exc).__name__}", file=sys.stderr)
        return 2
    if result.body:
        print(result.body)
    else:
        print(json.dumps({"status_code": result.status_code, "secret_exposed_to_model": False}, sort_keys=True))
    return 0 if 200 <= result.status_code < 300 else 1

"""DeepSeek provider key storage and runtime bridge activation.

The API key is durable only inside the encrypted OmniDoer Vault. Moon Bridge
receives a short-lived configuration under ``/run`` because it does not read
Vault records itself.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from omnidoer.omni_vault.vault import Vault
from omnidoer.paths import home


DEEPSEEK_ORIGIN = "https://api.deepseek.com"
DEEPSEEK_PROVIDER_ID = "deepseek"
DEEPSEEK_CREDENTIAL_KIND = "model_provider_api_key"
DEEPSEEK_COMPATIBLE_CREDENTIAL_KINDS = {DEEPSEEK_CREDENTIAL_KIND, "llm_api"}
DEEPSEEK_KEY_PLACEHOLDER = "__OMNIDOER_DEEPSEEK_API_KEY__"
DEFAULT_TEMPLATE_PATH = Path("/etc/omnidoer/moonbridge-deepseek.yml.template")
DEFAULT_RUNTIME_CONFIG_PATH = Path("/run/omnidoer-moonbridge/deepseek.yml")
DEFAULT_SERVICE_NAME = "omnidoer-moonbridge.service"


def _vault_path(vault_path: str | Path | None) -> Path:
    """Resolve the Vault without mutating its parent directory.

    The Moon Bridge systemd unit intentionally mounts the OmniDoer home
    read-only.  ``default_vault_path`` calls ``ensure_home`` for normal CLI
    use, which includes a chmod and therefore cannot be used by that unit.
    """
    return Path(vault_path) if vault_path else home() / "vault.json"


def _deepseek_credential_id(vault: Vault) -> str | None:
    for credential in vault.list_metadata():
        metadata = credential.metadata
        if (
            metadata.get("kind") in DEEPSEEK_COMPATIBLE_CREDENTIAL_KINDS
            and metadata.get("provider") == DEEPSEEK_PROVIDER_ID
            and DEEPSEEK_ORIGIN in credential.allowed_origins
        ):
            return credential.credential_id
    return None


def validate_api_key(api_key: str) -> str:
    value = str(api_key or "").strip()
    if len(value) < 16 or len(value) > 1024 or "\n" in value or "\r" in value or "\0" in value:
        raise ValueError("invalid DeepSeek API key")
    return value


def upsert_api_key(vault: Vault, api_key: str) -> tuple[str, bool]:
    value = validate_api_key(api_key)
    metadata = {
        "kind": DEEPSEEK_CREDENTIAL_KIND,
        "provider": DEEPSEEK_PROVIDER_ID,
        "name": "DeepSeek API Key",
        "source": "control_client_e2ee",
    }
    credential_id = _deepseek_credential_id(vault)
    if credential_id:
        vault.update_credential(
            credential_id,
            username=DEEPSEEK_PROVIDER_ID,
            password=value,
            allowed_origins=[DEEPSEEK_ORIGIN],
            metadata=metadata,
        )
        return credential_id, False
    return (
        vault.add_credential(
            username=DEEPSEEK_PROVIDER_ID,
            password=value,
            allowed_origins=[DEEPSEEK_ORIGIN],
            metadata=metadata,
        ),
        True,
    )


def provider_status(
    *,
    vault_path: str | Path | None = None,
    passphrase_available: bool = False,
    service_name: str = DEFAULT_SERVICE_NAME,
) -> dict[str, object]:
    path = _vault_path(vault_path)
    configured = path.exists() and _deepseek_credential_id(Vault.load(path)) is not None
    bridge_active = False
    try:
        bridge_active = subprocess.run(
            ["systemctl", "is-active", "--quiet", service_name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {
        "provider": DEEPSEEK_PROVIDER_ID,
        "configured": configured,
        "vault_ready": path.exists() and passphrase_available,
        "bridge_active": bridge_active,
        "secret_exposed_to_model": False,
    }


def _passphrase(*, vault_path: Path, passphrase: str | None, passphrase_file: str | Path | None) -> str:
    if passphrase:
        return passphrase
    path = Path(passphrase_file) if passphrase_file else vault_path.with_name("vault-passphrase")
    if not path.exists():
        raise FileNotFoundError("Vault passphrase source not found")
    return path.read_text(encoding="utf-8").splitlines()[0]


def prepare_runtime_config(
    *,
    vault_path: str | Path | None = None,
    passphrase: str | None = None,
    passphrase_file: str | Path | None = None,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
    output_path: str | Path = DEFAULT_RUNTIME_CONFIG_PATH,
) -> Path:
    vault_file = _vault_path(vault_path)
    vault = Vault.load(
        vault_file,
        _passphrase(vault_path=vault_file, passphrase=passphrase, passphrase_file=passphrase_file),
    )
    credential_id = _deepseek_credential_id(vault)
    if not credential_id:
        raise FileNotFoundError("DeepSeek key is not configured in Vault")
    api_key = validate_api_key(vault.decrypt_credential(credential_id).password)
    template = Path(template_path).read_text(encoding="utf-8")
    if DEEPSEEK_KEY_PLACEHOLDER not in template:
        raise ValueError("DeepSeek bridge template has no key placeholder")
    rendered = template.replace(DEEPSEEK_KEY_PLACEHOLDER, json.dumps(api_key)[1:-1], 1)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    target.parent.chmod(0o700)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, target)
    target.chmod(0o600)
    return target


def activate_bridge(**prepare_kwargs) -> dict[str, object]:
    prepare_runtime_config(**prepare_kwargs)
    result = subprocess.run(
        ["systemctl", "restart", DEFAULT_SERVICE_NAME],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
    )
    return {"bridge_active": result.returncode == 0, "secret_exposed_to_model": False}


def handle_provider_command(args) -> int:
    if args.provider_name != DEEPSEEK_PROVIDER_ID:
        return 2
    if args.provider_command == "prepare-runtime":
        target = prepare_runtime_config(
            vault_path=args.vault,
            passphrase_file=args.passphrase_file,
            template_path=args.template,
            output_path=args.output,
        )
        print(f"DeepSeek runtime bridge configuration prepared: {target}")
        print("secret_exposed_to_model=false")
        return 0
    return 2

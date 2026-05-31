"""Secret Broker actions.

Broker methods return status only. They do not return decrypted secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, decrypt_control_envelope
from omnidoer.omni_policy.policy import evaluate_credential_fill
from omnidoer.omni_vault.models import CredentialSecret
from omnidoer.omni_vault.vault import Vault


@dataclass
class FillResult:
    status: str
    origin: str
    fields: list[str]
    saved_to_vault: bool = False
    secret_exposed_to_model: bool = False

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "origin": self.origin,
            "fields": self.fields,
            "saved_to_vault": self.saved_to_vault,
            "secret_exposed_to_model": False,
        }


def validate_fill(current_url: str, allowed_origins: list[str], form_action_url: str | None = None, top_level_frame: bool = True):
    decision = evaluate_credential_fill(
        current_url=current_url,
        allowed_origins=set(allowed_origins),
        top_level_frame=top_level_frame,
        form_action_url=form_action_url,
    )
    if decision.decision != "allow":
        raise PermissionError(decision.reason)
    return decision


def fill_login_status(current_url: str, allowed_origins: list[str], secret: CredentialSecret) -> FillResult:
    decision = validate_fill(current_url, allowed_origins)
    # The browser injection happens outside this pure status helper.
    return FillResult(status="credential_received_and_filled", origin=decision.origin or "", fields=["username", "password"])


def should_save_to_vault(request, payload: dict[str, Any]) -> bool:
    return request.save_to_vault and payload.get("save_to_vault") is True


class SecretBroker:
    """Controlled in-process secret use for Control Client credential requests."""

    def __init__(
        self,
        *,
        store: RequestStore | None = None,
        vault_path: str | Path | None = None,
        vault_passphrase: str | None = None,
        replay_guard: ReplayGuard | None = None,
        audit: AuditLog | None = None,
    ):
        self.store = store or RequestStore()
        self.vault_path = Path(vault_path) if vault_path else None
        self.vault_passphrase = vault_passphrase
        self.replay_guard = replay_guard
        self.audit = audit or AuditLog()
        self._payloads: dict[str, dict[str, Any]] = {}

    def receive_from_control_client(self, request_id: str) -> dict:
        request = self.store.get(request_id)
        if request.request_type != "credential":
            raise ValueError("request is not a credential request")
        if not request.response_ciphertext:
            raise ValueError("credential request has no encrypted response")
        expected_device_id = request.allowed_device_id
        expected_expires_at = request.expires_at if request.response_ciphertext.get("expires_at") is not None else None
        payload = decrypt_control_envelope(
            request.response_ciphertext,
            request_id=request.request_id,
            origin=request.origin,
            request_type=request.request_type,
            device_id=expected_device_id,
            expires_at=expected_expires_at,
            replay_guard=self.replay_guard,
        )
        self._payloads[request_id] = payload
        fields = [field for field in ("username", "password", "totp_seed") if payload.get(field)]
        self.audit.append("credential_received", request_id=request_id, origin=request.origin, fields=fields, status="ok")
        return {
            "status": "credential_received",
            "request_id": request_id,
            "origin": request.origin,
            "fields": fields,
            "secret_exposed_to_model": False,
        }

    def store_or_use_once(self, request_id: str) -> dict:
        request = self.store.get(request_id)
        payload = self._payloads.get(request_id)
        if payload is None:
            self.receive_from_control_client(request_id)
            payload = self._payloads[request_id]
        saved_to_vault = False
        credential_id = None
        if should_save_to_vault(request, payload):
            if self.vault_path is None or self.vault_passphrase is None:
                raise ValueError("vault path and passphrase are required to save credentials")
            vault = Vault.load(self.vault_path, self.vault_passphrase)
            credential_id = vault.add_credential(
                username=str(payload.get("username") or ""),
                password=str(payload.get("password") or ""),
                totp_seed=payload.get("totp_seed") or None,
                allowed_origins=[request.origin],
            )
            saved_to_vault = True
            self.audit.append("credential_saved", request_id=request_id, origin=request.origin, credential_id=credential_id, status="ok")
        return {
            "status": "credential_saved" if saved_to_vault else "credential_ready_for_one_time_use",
            "request_id": request_id,
            "origin": request.origin,
            "credential_id": credential_id,
            "saved_to_vault": saved_to_vault,
            "secret_exposed_to_model": False,
        }

    def fill_after_receive(
        self,
        request_id: str,
        *,
        browser_controller,
        username_selector: str = "input[autocomplete='username'], input[name='email'], input[name='username'], input[name='acct'], #email, #username",
        password_selector: str = "input[type='password']",
    ) -> dict:
        request = self.store.get(request_id)
        payload = self._payloads.get(request_id)
        if payload is None:
            self.receive_from_control_client(request_id)
            payload = self._payloads[request_id]
        validate_fill(browser_controller.current_url(), [request.origin], browser_controller.inspect_form_action())
        browser_controller.fill_field(username_selector, str(payload.get("username") or ""), secret=True)
        browser_controller.fill_field(password_selector, str(payload.get("password") or ""), secret=True)
        self.audit.append("credential_filled", request_id=request_id, origin=request.origin, fields=["username", "password"], status="ok")
        return {
            "status": "credential_received_and_filled",
            "origin": request.origin,
            "fields": ["username", "password"],
            "saved_to_vault": False,
            "secret_exposed_to_model": False,
        }

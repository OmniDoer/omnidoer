"""Secret Broker actions.

Broker methods return status only. They do not return decrypted secrets.
"""

from __future__ import annotations

from dataclasses import dataclass

from omnidoer.omni_policy.policy import evaluate_credential_fill
from omnidoer.omni_vault.models import CredentialSecret


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

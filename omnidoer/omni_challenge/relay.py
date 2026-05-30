"""Challenge Relay.

Challenge answers are handled as encrypted payloads or user-completed status.
They are never returned to the model.
"""

from __future__ import annotations

import os

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import ControlRequest, RequestStore


def request_user_interaction(
    *,
    origin: str,
    top_level_url: str,
    challenge_type: str,
    reason: str,
    fields: list[str] | None = None,
    risk_level: str = "medium",
    store: RequestStore | None = None,
) -> ControlRequest:
    store = store or RequestStore()
    request_type = {
        "sms": "sms_code",
        "email": "email_code",
        "3ds": "payment_3ds",
    }.get(challenge_type, challenge_type)
    request = store.create(
        request_type,
        origin=origin,
        top_level_url=top_level_url,
        action_summary=reason,
        risk_level=risk_level,
        requested_fields=fields or [],
        challenge_type=challenge_type,
    )
    AuditLog().append(
        "challenge_requested",
        request_id=request.request_id,
        origin=origin,
        challenge_type=challenge_type,
        risk_level=risk_level,
        status=request.status,
    )
    return request


def complete_in_test_mode(request_id: str, *, store: RequestStore | None = None) -> dict:
    store = store or RequestStore()
    request = store.get(request_id)
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") != "1":
        raise RuntimeError("challenge test mode is not enabled")
    completed = store.mark_challenge_completed(request_id)
    AuditLog().append(
        "challenge_completed",
        request_id=request_id,
        origin=request.origin,
        challenge_type=request.challenge_type,
        completed_by_user=True,
        bypassed=False,
        status=completed.status,
    )
    return {
        "status": "challenge_completed",
        "origin": request.origin,
        "challenge_type": request.challenge_type,
        "completed_by_user": True,
        "bypassed": False,
        "secret_exposed_to_model": False,
    }

"""Human approval gate."""

from __future__ import annotations

import os

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import ControlRequest, RequestStore


def request_approval(
    *,
    origin: str,
    top_level_url: str,
    action_summary: str,
    risk_level: str,
    structured_details: dict,
    store: RequestStore | None = None,
) -> ControlRequest:
    store = store or RequestStore()
    return store.create(
        "payment_approval",
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        risk_level=risk_level,
        requested_fields=sorted(structured_details.keys()),
        structured_details=structured_details,
    )


def decide(request_id: str, *, store: RequestStore | None = None) -> str:
    store = store or RequestStore()
    mode = os.environ.get("OMNIDOER_APPROVAL_MODE", "interactive")
    if mode == "approve":
        request = store.approve(request_id)
    elif mode == "deny":
        request = store.deny(request_id)
    else:
        answer = input("Approve this action? [y/N]: ").strip().lower()
        request = store.approve(request_id) if answer == "y" else store.deny(request_id)
    AuditLog().append(
        "approval_decision",
        request_id=request.request_id,
        origin=request.origin,
        risk_level=request.risk_level,
        decision=request.approval_decision,
        status=request.status,
    )
    return request.approval_decision or "unknown"

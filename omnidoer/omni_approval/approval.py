"""Human approval gate."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import ControlRequest, RequestStore


APPROVAL_SCOPE_FIELDS = (
    "sensitive_action_type",
    "merchant",
    "payee",
    "recipient",
    "amount",
    "currency",
    "item_summary",
    "service_summary",
    "payment_method_summary",
    "billing_method_summary",
    "origin",
    "form_action",
    "form_action_origin",
    "final_button",
    "subscription",
    "renewal",
    "refund_terms",
    "cancellation_terms",
    "after_approval",
)


def _normalize_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool | int | float | str):
        return str(value).strip()
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_value(value[key]) for key in sorted(value)}
    return str(value).strip()


def approval_scope(
    *,
    origin: str,
    top_level_url: str,
    action_summary: str,
    structured_details: dict[str, Any],
) -> dict[str, Any]:
    # Fingerprint raw reviewed details so redacted public fields still detect changes.
    scope: dict[str, Any] = {
        "origin": _normalize_value(origin),
        "top_level_url": _normalize_value(top_level_url),
        "action_summary": _normalize_value(action_summary),
    }
    for key in APPROVAL_SCOPE_FIELDS:
        if key in structured_details:
            scope[key] = _normalize_value(structured_details[key])
    return scope


def approval_fingerprint(
    *,
    origin: str,
    top_level_url: str,
    action_summary: str,
    structured_details: dict[str, Any],
) -> str:
    scope = approval_scope(
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        structured_details=structured_details,
    )
    payload = json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


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
    fingerprint = approval_fingerprint(
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        structured_details=structured_details,
    )
    return store.create(
        "payment_approval",
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        risk_level=risk_level,
        requested_fields=sorted(structured_details.keys()),
        structured_details=structured_details,
        approval_fingerprint=fingerprint,
    )


def verify_approval_scope(
    request_id: str,
    *,
    origin: str,
    top_level_url: str,
    action_summary: str,
    structured_details: dict[str, Any],
    store: RequestStore | None = None,
    consume: bool = False,
) -> ControlRequest:
    store = store or RequestStore()
    request = store.get(request_id)
    if request.status != "approved":
        raise PermissionError("approval request is not approved")
    if request.used:
        raise PermissionError("approval request already used")
    expected = request.approval_fingerprint
    current = approval_fingerprint(
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        structured_details=structured_details,
    )
    if expected and current != expected:
        raise PermissionError("approval scope changed after user review")
    if not expected:
        raise PermissionError("approval fingerprint is required for scoped sensitive actions")
    if request.origin != origin:
        raise PermissionError("approval origin mismatch")
    if consume:
        return store.consume_approval(request_id)
    return request


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

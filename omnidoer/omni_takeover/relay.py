"""Human Takeover Relay."""

from __future__ import annotations

import os

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import ControlRequest, RequestStore
from omnidoer.omni_takeover.input_events import parse_actions, validate_input_event
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.stream import current_frame


def request_user_control(
    *,
    origin: str,
    top_level_url: str,
    reason: str,
    browser_context_id: str = "demo",
    risk_level: str = "high",
    store: RequestStore | None = None,
) -> ControlRequest:
    store = store or RequestStore()
    request = store.create(
        "human_takeover",
        origin=origin,
        top_level_url=top_level_url,
        action_summary=reason,
        risk_level=risk_level,
        takeover_reason=reason,
        browser_context_id=browser_context_id,
    )
    AuditLog().append(
        "takeover_started",
        request_id=request.request_id,
        origin=origin,
        takeover_reason=reason,
        risk_level=risk_level,
        status=request.status,
    )
    return request


def request_registration_handoff(
    *,
    origin: str,
    top_level_url: str,
    reason: str = "user account registration required",
    browser_context_id: str = "demo",
    risk_level: str = "medium",
    allowed_device_id: str | None = None,
    store: RequestStore | None = None,
) -> ControlRequest:
    store = store or RequestStore()
    request = store.create(
        "account_registration",
        origin=origin,
        top_level_url=top_level_url,
        action_summary=reason,
        risk_level=risk_level,
        takeover_reason=reason,
        browser_context_id=browser_context_id,
        allowed_device_id=allowed_device_id,
        structured_details={
            "handoff_type": "account_registration",
            "agent_status": "paused",
            "completed_by": "user",
            "bulk_or_fake_registration": False,
            "secret_exposed_to_model": False,
        },
    )
    AuditLog().append(
        "registration_handoff_started",
        request_id=request.request_id,
        origin=origin,
        takeover_reason=reason,
        risk_level=risk_level,
        status=request.status,
    )
    return request


def start_stream(request_id: str, *, browser_controller=None, store: RequestStore | None = None) -> dict:
    store = store or RequestStore()
    request = store.get(request_id)
    if request.request_type not in {"human_takeover", "account_registration"}:
        raise ValueError("not a takeover or registration handoff request")
    if request.status != "user_control":
        raise ValueError("user is not in control")
    if browser_controller is not None:
        return browser_controller.takeover_frame()
    return current_frame()


def apply_input_event(request_id: str, event: InputEvent, *, browser_controller=None, store: RequestStore | None = None) -> dict:
    store = store or RequestStore()
    request = store.get(request_id)
    if request.status != "user_control":
        raise ValueError("user is not in control")
    validate_input_event(event)
    result = {"status": "event_applied", "secret_exposed_to_model": False}
    if browser_controller is not None:
        result = browser_controller.apply_user_input_event(event)
    # Do not log event text or sensitive inputs.
    AuditLog().append(
        "takeover_input_event",
        request_id=request_id,
        origin=request.origin,
        input_event_type=getattr(event, "event_type", "unknown"),
    )
    return {**result, "secret_exposed_to_model": False}


def release_control(request_id: str, *, store: RequestStore | None = None) -> dict:
    store = store or RequestStore()
    request = store.release_takeover(request_id)
    AuditLog().append(
        "takeover_released",
        request_id=request.request_id,
        origin=request.origin,
        takeover_reason=request.takeover_reason,
        status=request.status,
    )
    return {
        "status": "user_completed_takeover",
        "completed_by_user": True,
        "bypassed": False,
        "secret_exposed_to_model": False,
    }


def complete_in_test_mode(request_id: str, *, browser_controller=None) -> dict:
    if os.environ.get("OMNIDOER_TAKEOVER_TEST_MODE") != "1":
        raise RuntimeError("takeover test mode is not enabled")
    for event in parse_actions(os.environ.get("OMNIDOER_TEST_TAKEOVER_ACTIONS", "release")):
        if event.event_type == "release":
            return release_control(request_id)
        apply_input_event(request_id, event, browser_controller=browser_controller)
    return release_control(request_id)

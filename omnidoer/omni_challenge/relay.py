"""Challenge Relay.

Challenge answers are handled as encrypted payloads or user-completed status.
They are never returned to the model.
"""

from __future__ import annotations

import os
from typing import Any

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_control.requests import ControlRequest, RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, decrypt_control_envelope


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


class ChallengeRelay:
    """Controlled challenge-answer handling for user-completed codes."""

    def __init__(
        self,
        *,
        store: RequestStore | None = None,
        replay_guard: ReplayGuard | None = None,
        audit: AuditLog | None = None,
    ):
        self.store = store or RequestStore()
        self.replay_guard = replay_guard
        self.audit = audit or AuditLog()
        self._payloads: dict[str, dict[str, Any]] = {}

    def receive_user_response(self, request_id: str) -> dict:
        request = self.store.get(request_id)
        if request.request_type not in {"totp", "sms_code", "email_code", "one_time_code", "payment_3ds"}:
            raise ValueError("request is not a user challenge response")
        if not request.response_ciphertext:
            raise ValueError("challenge request has no encrypted response")
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
        fields = [field for field in ("code", "otp", "ack") if payload.get(field)]
        self.audit.append(
            "challenge_response_received",
            request_id=request_id,
            origin=request.origin,
            challenge_type=request.challenge_type,
            fields=fields,
            status="ok",
        )
        return {
            "status": "challenge_response_received",
            "request_id": request_id,
            "origin": request.origin,
            "challenge_type": request.challenge_type,
            "fields": fields,
            "secret_exposed_to_model": False,
        }

    def inject_response_if_applicable(self, request_id: str, *, browser_controller, selector: str | None = None) -> dict:
        request = self.store.get(request_id)
        payload = self._payloads.get(request_id)
        if payload is None:
            self.receive_user_response(request_id)
            payload = self._payloads[request_id]
        value = payload.get("code") or payload.get("otp") or payload.get("ack")
        if not value:
            raise ValueError("challenge payload has no injectable value")
        target_selector = selector or self._default_selector(request)
        browser_controller.fill_field(target_selector, str(value), secret=True)
        completed = self.store.mark_challenge_completed(request_id)
        self.audit.append(
            "challenge_response_injected",
            request_id=request_id,
            origin=request.origin,
            challenge_type=request.challenge_type,
            completed_by_user=True,
            bypassed=False,
            status=completed.status,
        )
        return {
            "status": "challenge_response_injected",
            "origin": request.origin,
            "challenge_type": request.challenge_type,
            "completed_by_user": True,
            "bypassed": False,
            "secret_exposed_to_model": False,
        }

    def mark_completed_by_user(self, request_id: str) -> dict:
        request = self.store.mark_challenge_completed(request_id)
        self.audit.append(
            "challenge_completed",
            request_id=request_id,
            origin=request.origin,
            challenge_type=request.challenge_type,
            completed_by_user=True,
            bypassed=False,
            status=request.status,
        )
        return {
            "status": "challenge_completed",
            "origin": request.origin,
            "challenge_type": request.challenge_type,
            "completed_by_user": True,
            "bypassed": False,
            "secret_exposed_to_model": False,
        }

    @staticmethod
    def _default_selector(request: ControlRequest) -> str:
        selectors = []
        for field in request.requested_fields:
            selectors.extend([f"#{field}", f"input[name='{field}']"])
        selectors.extend(["input[autocomplete='one-time-code']", "#otp", "input[name='otp']", "#code", "input[name='code']", "#ack"])
        return ", ".join(selectors)

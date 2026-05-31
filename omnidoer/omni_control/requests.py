"""Control, challenge, approval, and takeover request store."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_observer.redactor import redact_dom_snapshot
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.paths import state_file


REQUEST_TYPES = {
    "credential",
    "totp",
    "one_time_code",
    "sms_code",
    "email_code",
    "captcha",
    "passkey",
    "webauthn",
    "device_confirmation",
    "payment_3ds",
    "human_takeover",
    "payment_approval",
    "oauth_approval",
    "account_delete",
    "password_change",
    "two_factor_change",
    "file_upload",
    "message_send",
    "account_registration",
}

EXPIRABLE_STATUSES = {"pending", "user_control", "fulfilled", "approved"}
TAKEOVER_FRAME_MAX_AGE_SECONDS = 30.0
COMPLETED_REQUEST_STATUSES = {"fulfilled", "approved", "denied", "released", "challenge_completed"}
ABORTED_REQUEST_STATUSES = {"denied", "expired", "cancelled", "rejected", "failed"}


@dataclass
class ControlRequest:
    request_id: str
    request_type: str
    origin: str
    top_level_url: str
    action_summary: str
    risk_level: str = "low"
    expires_at: float = field(default_factory=lambda: time.time() + 300)
    status: str = "pending"
    broker_public_key_fingerprint: str | None = None
    one_time_use: bool = True
    save_to_vault: bool = False
    requested_fields: list[str] = field(default_factory=list)
    challenge_type: str | None = None
    takeover_reason: str | None = None
    browser_context_id: str | None = None
    takeover_frame_id: str | None = None
    takeover_frame_captured_at: float | None = None
    takeover_frame_viewport_width: int | None = None
    takeover_frame_viewport_height: int | None = None
    allowed_device_id: str | None = None
    control_owner: str = "agent"
    structured_details: dict[str, Any] = field(default_factory=dict)
    response_ciphertext: dict[str, Any] | None = None
    approval_decision: str | None = None
    approval_fingerprint: str | None = None
    completed_by_user: bool = False
    bypassed: bool = False
    used: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) > self.expires_at

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("response_ciphertext", None)
        data["structured_details"] = redact_dom_snapshot(data.get("structured_details") or {})
        data["secret_exposed_to_model"] = False
        return data


class RequestStore:
    def __init__(self, path: Path | None = None, *, audit: AuditLog | None = None):
        self.path = path or state_file("control_requests.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.audit = audit or AuditLog(self.path.with_name("audit.log") if path is not None else None)

    def _load(self) -> dict[str, ControlRequest]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: ControlRequest(**value) for key, value in raw.items()}

    def _save(self, requests: dict[str, ControlRequest]) -> None:
        serializable = {key: asdict(value) for key, value in requests.items()}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(serializable, indent=2, sort_keys=True))
        tmp.replace(self.path)
        self.path.chmod(0o600)

    def _audit_transition(self, event_type: str, request: ControlRequest, *, previous_status: str | None = None) -> None:
        self.audit.append(
            event_type,
            request_id=request.request_id,
            request_type=request.request_type,
            origin=request.origin,
            previous_status=previous_status,
            status=request.status,
            completed_by_user=request.completed_by_user,
            has_ciphertext=request.response_ciphertext is not None,
        )

    def _expire_if_needed(self, request: ControlRequest) -> bool:
        if request.status in EXPIRABLE_STATUSES and request.is_expired():
            request.status = "expired"
            request.updated_at = time.time()
            return True
        return False

    def list(self, include_expired: bool = False) -> list[ControlRequest]:
        requests = self._load()
        for request in requests.values():
            self._expire_if_needed(request)
        self._save(requests)
        values = list(requests.values())
        if include_expired:
            return values
        return [request for request in values if request.status != "expired"]

    def create(
        self,
        request_type: str,
        *,
        origin: str,
        top_level_url: str,
        action_summary: str,
        risk_level: str = "low",
        ttl_seconds: int = 300,
        broker_public_key_fingerprint: str | None = None,
        requested_fields: list[str] | None = None,
        challenge_type: str | None = None,
        takeover_reason: str | None = None,
        browser_context_id: str | None = None,
        allowed_device_id: str | None = None,
        save_to_vault: bool = False,
        structured_details: dict[str, Any] | None = None,
        approval_fingerprint: str | None = None,
    ) -> ControlRequest:
        if request_type not in REQUEST_TYPES:
            raise ValueError(f"unsupported request type: {request_type}")
        request = ControlRequest(
            request_id=f"req_{uuid.uuid4().hex}",
            request_type=request_type,
            origin=origin,
            top_level_url=top_level_url,
            action_summary=action_summary,
            risk_level=risk_level,
            expires_at=time.time() + ttl_seconds,
            broker_public_key_fingerprint=broker_public_key_fingerprint,
            requested_fields=requested_fields or [],
            challenge_type=challenge_type,
            takeover_reason=takeover_reason,
            browser_context_id=browser_context_id,
            allowed_device_id=allowed_device_id,
            save_to_vault=save_to_vault,
            structured_details=dict(structured_details or {}),
            approval_fingerprint=approval_fingerprint,
        )
        if request_type in {"human_takeover", "account_registration"}:
            request.control_owner = "user"
            request.status = "user_control"
        requests = self._load()
        requests[request.request_id] = request
        self._save(requests)
        self._audit_transition("control_request_created", request)
        return request

    def get(self, request_id: str) -> ControlRequest:
        requests = self._load()
        try:
            request = requests[request_id]
        except KeyError as exc:
            raise KeyError(f"request not found: {request_id}") from exc
        if self._expire_if_needed(request):
            requests[request_id] = request
            self._save(requests)
        return request

    def update(self, request: ControlRequest) -> ControlRequest:
        requests = self._load()
        previous = requests.get(request.request_id)
        previous_status = previous.status if previous else None
        had_ciphertext = previous.response_ciphertext is not None if previous else False
        request.updated_at = time.time()
        requests[request.request_id] = request
        self._save(requests)
        became_terminal = previous_status != request.status and request.status in COMPLETED_REQUEST_STATUSES | {"expired"}
        received_ciphertext = not had_ciphertext and request.response_ciphertext is not None
        if became_terminal or received_ciphertext:
            self._audit_transition("control_request_completed", request, previous_status=previous_status)
        return request

    def _ensure_actionable(self, request: ControlRequest, *, allow_fulfilled: bool = False) -> None:
        if request.is_expired():
            request.status = "expired"
            self.update(request)
            raise ValueError("request expired")
        if request.used and not (allow_fulfilled and request.status == "fulfilled"):
            raise ValueError("request already used")

    def submit_ciphertext(self, request_id: str, envelope: dict[str, Any]) -> ControlRequest:
        request = self.get(request_id)
        self._ensure_actionable(request)
        if request.response_ciphertext is not None:
            raise ValueError("request already used")
        request.response_ciphertext = envelope
        request.status = "fulfilled"
        request.used = request.one_time_use
        request.completed_by_user = True
        return self.update(request)

    def approve(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        self._ensure_actionable(request)
        request.approval_decision = "approved"
        request.status = "approved"
        request.used = False
        request.completed_by_user = True
        return self.update(request)

    def deny(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        self._ensure_actionable(request)
        request.approval_decision = "denied"
        request.status = "denied"
        request.used = request.one_time_use
        request.completed_by_user = True
        return self.update(request)

    def mark_challenge_completed(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        self._ensure_actionable(request, allow_fulfilled=True)
        request.status = "challenge_completed"
        request.completed_by_user = True
        request.bypassed = False
        request.used = request.one_time_use
        return self.update(request)

    def release_takeover(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        if request.request_type not in {"human_takeover", "account_registration"}:
            raise ValueError("request is not human takeover or registration handoff")
        self._ensure_actionable(request)
        request.status = "released"
        request.control_owner = "agent"
        request.completed_by_user = True
        request.bypassed = False
        request.used = request.one_time_use
        return self.update(request)

    def record_takeover_frame(self, request_id: str, frame: dict[str, Any]) -> ControlRequest:
        request = self.get(request_id)
        if request.request_type not in {"human_takeover", "account_registration"}:
            raise ValueError("request is not human takeover or registration handoff")
        self._ensure_actionable(request)
        viewport = frame.get("viewport") or {}
        request.takeover_frame_id = str(frame.get("frame_id") or "")
        request.takeover_frame_captured_at = float(frame.get("captured_at") or time.time())
        request.takeover_frame_viewport_width = int(viewport.get("width") or 0) or None
        request.takeover_frame_viewport_height = int(viewport.get("height") or 0) or None
        return self.update(request)

    def validate_takeover_frame(self, request_id: str, frame_id: str | None, *, now: float | None = None) -> ControlRequest:
        request = self.get(request_id)
        if request.request_type not in {"human_takeover", "account_registration"}:
            raise ValueError("request is not human takeover or registration handoff")
        self._ensure_actionable(request)
        if not request.takeover_frame_id:
            return request
        if not frame_id or frame_id != request.takeover_frame_id:
            raise ValueError("stale takeover frame")
        captured_at = request.takeover_frame_captured_at or 0.0
        if (now or time.time()) - captured_at > TAKEOVER_FRAME_MAX_AGE_SECONDS:
            raise ValueError("stale takeover frame")
        return request

    def validate_takeover_input(self, request_id: str, event: InputEvent, *, now: float | None = None) -> ControlRequest:
        request = self.validate_takeover_frame(request_id, event.frame_id, now=now)
        width = request.takeover_frame_viewport_width
        height = request.takeover_frame_viewport_height
        if not width or not height:
            return request

        def in_bounds(x: int | None, y: int | None) -> bool:
            return x is not None and y is not None and 0 <= x < width and 0 <= y < height

        if event.event_type in {"tap", "click", "double_click", "long_press"} and not in_bounds(event.x, event.y):
            raise ValueError("takeover coordinates out of frame bounds")
        if event.event_type == "drag" and (not in_bounds(event.x, event.y) or not in_bounds(event.to_x, event.to_y)):
            raise ValueError("takeover coordinates out of frame bounds")
        return request

    def consume_approval(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        self._ensure_actionable(request)
        if request.status != "approved" or request.approval_decision != "approved":
            raise ValueError("approval request is not approved")
        request.status = "consumed"
        request.used = True
        return self.update(request)


def wait_for_request_completion(
    request_id: str,
    *,
    store: RequestStore | None = None,
    timeout_seconds: float = 300,
    poll_interval_seconds: float = 0.5,
    require_ciphertext: bool = False,
    terminal_statuses: set[str] | None = None,
) -> ControlRequest:
    """Wait until a user-driven Control Request reaches an actionable state.

    The returned request is still public-safe by default. Callers that need to
    use encrypted payloads must pass them to the Broker/Challenge Relay instead
    of returning decrypted fields to the model.
    """

    store = store or RequestStore()
    deadline = time.time() + timeout_seconds
    statuses = terminal_statuses or COMPLETED_REQUEST_STATUSES
    while time.time() < deadline:
        request = store.get(request_id)
        if request.response_ciphertext is not None:
            return request
        if request.status in statuses and not require_ciphertext:
            return request
        if request.status in ABORTED_REQUEST_STATUSES:
            return request
        time.sleep(poll_interval_seconds)
    raise TimeoutError("timed out waiting for Control Client request")

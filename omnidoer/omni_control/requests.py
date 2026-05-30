"""Control, challenge, approval, and takeover request store."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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
}


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
    control_owner: str = "agent"
    response_ciphertext: dict[str, Any] | None = None
    approval_decision: str | None = None
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
        data["secret_exposed_to_model"] = False
        return data


class RequestStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_requests.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

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

    def list(self, include_expired: bool = False) -> list[ControlRequest]:
        requests = self._load()
        for request in requests.values():
            if request.status == "pending" and request.is_expired():
                request.status = "expired"
                request.updated_at = time.time()
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
        save_to_vault: bool = False,
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
            save_to_vault=save_to_vault,
        )
        if request_type == "human_takeover":
            request.control_owner = "user"
            request.status = "user_control"
        requests = self._load()
        requests[request.request_id] = request
        self._save(requests)
        return request

    def get(self, request_id: str) -> ControlRequest:
        requests = self._load()
        try:
            request = requests[request_id]
        except KeyError as exc:
            raise KeyError(f"request not found: {request_id}") from exc
        if request.status == "pending" and request.is_expired():
            request.status = "expired"
            request.updated_at = time.time()
            requests[request_id] = request
            self._save(requests)
        return request

    def update(self, request: ControlRequest) -> ControlRequest:
        requests = self._load()
        request.updated_at = time.time()
        requests[request.request_id] = request
        self._save(requests)
        return request

    def submit_ciphertext(self, request_id: str, envelope: dict[str, Any]) -> ControlRequest:
        request = self.get(request_id)
        if request.is_expired():
            request.status = "expired"
            self.update(request)
            raise ValueError("request expired")
        if request.used or request.response_ciphertext is not None:
            raise ValueError("request already used")
        request.response_ciphertext = envelope
        request.status = "fulfilled"
        request.used = request.one_time_use
        request.completed_by_user = True
        return self.update(request)

    def approve(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        if request.used:
            raise ValueError("request already used")
        request.approval_decision = "approved"
        request.status = "approved"
        request.used = request.one_time_use
        request.completed_by_user = True
        return self.update(request)

    def deny(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        if request.used:
            raise ValueError("request already used")
        request.approval_decision = "denied"
        request.status = "denied"
        request.used = request.one_time_use
        request.completed_by_user = True
        return self.update(request)

    def mark_challenge_completed(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        request.status = "challenge_completed"
        request.completed_by_user = True
        request.bypassed = False
        request.used = request.one_time_use
        return self.update(request)

    def release_takeover(self, request_id: str) -> ControlRequest:
        request = self.get(request_id)
        if request.request_type != "human_takeover":
            raise ValueError("request is not human takeover")
        request.status = "released"
        request.control_owner = "agent"
        request.completed_by_user = True
        request.bypassed = False
        request.used = request.one_time_use
        return self.update(request)

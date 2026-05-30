"""Short-lived Control Client sessions."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from omnidoer.paths import state_file


@dataclass
class ControlSession:
    session_id: str
    device_id: str
    token_hash: str
    csrf_token: str
    expires_at: float
    revoked: bool = False
    created_at: float = field(default_factory=time.time)
    last_seen_at: float | None = None

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) > self.expires_at

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
        }


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SessionStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_sessions.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, ControlSession]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: ControlSession(**value) for key, value in raw.items()}

    def _save(self, sessions: dict[str, ControlSession]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({key: asdict(value) for key, value in sessions.items()}, indent=2, sort_keys=True))
        tmp.replace(self.path)
        self.path.chmod(0o600)

    def create(self, *, device_id: str, ttl_seconds: int = 86400) -> tuple[ControlSession, str]:
        token = secrets.token_urlsafe(32)
        session = ControlSession(
            session_id=f"sess_{uuid.uuid4().hex}",
            device_id=device_id,
            token_hash=hash_session_token(token),
            csrf_token=secrets.token_urlsafe(24),
            expires_at=time.time() + ttl_seconds,
        )
        sessions = self._load()
        sessions[session.session_id] = session
        self._save(sessions)
        return session, token

    def list(self) -> list[ControlSession]:
        return sorted(self._load().values(), key=lambda item: item.created_at)

    def revoke(self, session_id: str) -> ControlSession:
        sessions = self._load()
        session = sessions[session_id]
        session.revoked = True
        sessions[session_id] = session
        self._save(sessions)
        return session

    def authenticate(self, session_id: str, token: str) -> ControlSession:
        sessions = self._load()
        try:
            session = sessions[session_id]
        except KeyError as exc:
            raise PermissionError("session not found") from exc
        if session.revoked or session.is_expired():
            raise PermissionError("session expired or revoked")
        if session.token_hash != hash_session_token(token):
            raise PermissionError("session token mismatch")
        session.last_seen_at = time.time()
        sessions[session.session_id] = session
        self._save(sessions)
        return session

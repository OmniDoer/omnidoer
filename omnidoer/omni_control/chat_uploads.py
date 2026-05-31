"""Temporary uploaded files for Control Client chat messages."""

from __future__ import annotations

import mimetypes
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from omnidoer.omni_control.pairing import parse_duration_seconds
from omnidoer.paths import state_file


DEFAULT_CHAT_UPLOAD_TTL_SECONDS = 24 * 60 * 60
DEFAULT_CHAT_UPLOAD_DIR_NAME = "control_chat_uploads"
MAX_CHAT_UPLOAD_BYTES = 64 * 1024 * 1024
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@dataclass
class ChatUpload:
    upload_id: str
    filename: str
    path: str
    size: int
    content_type: str
    created_at: float
    expires_at: float

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def chat_upload_dir() -> Path:
    configured = os.environ.get("OMNIDOER_CHAT_UPLOAD_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return state_file(DEFAULT_CHAT_UPLOAD_DIR_NAME)


def chat_upload_ttl_seconds(value: str | int | None = None) -> int:
    configured = value if value is not None else os.environ.get("OMNIDOER_CHAT_UPLOAD_TTL")
    return max(60, parse_duration_seconds(configured, default=DEFAULT_CHAT_UPLOAD_TTL_SECONDS))


def normalize_attachments(attachments: Any) -> list[dict[str, Any]]:
    if not isinstance(attachments, list):
        return []
    normalized: list[dict[str, Any]] = []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue
        filename = str(attachment.get("filename") or "").strip()
        path = str(attachment.get("path") or "").strip()
        if not filename or not path:
            continue
        try:
            size = int(attachment.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        normalized.append(
            {
                "upload_id": str(attachment.get("upload_id") or ""),
                "filename": filename,
                "path": path,
                "size": max(0, size),
                "content_type": str(attachment.get("content_type") or ""),
                "created_at": float(attachment.get("created_at") or 0.0),
                "expires_at": float(attachment.get("expires_at") or 0.0),
            }
        )
    return normalized


def validate_uploaded_attachments(attachments: Any, directory: Path | None = None) -> list[dict[str, Any]]:
    base = (directory or chat_upload_dir()).resolve()
    validated = []
    for attachment in normalize_attachments(attachments):
        path = Path(str(attachment["path"])).expanduser().resolve()
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise ValueError("chat attachment path is outside upload directory") from exc
        if not path.is_file():
            raise ValueError("chat attachment file is missing")
        attachment["path"] = str(path)
        attachment["size"] = path.stat().st_size
        validated.append(attachment)
    return validated


def attachment_summary_text(attachments: Any) -> str:
    normalized = normalize_attachments(attachments)
    if not normalized:
        return ""
    lines = ["[Attachments]"]
    for attachment in normalized:
        lines.append(f"- filename: {attachment['filename']}")
        lines.append(f"  path: {attachment['path']}")
        lines.append(f"  size: {attachment['size']} bytes")
        if attachment.get("content_type"):
            lines.append(f"  content_type: {attachment['content_type']}")
        if attachment.get("expires_at"):
            lines.append(f"  expires_at: {attachment['expires_at']}")
    return "\n".join(lines)


def append_attachments_to_text(text: str, attachments: Any) -> str:
    cleaned = text.strip()
    summary = attachment_summary_text(attachments)
    if not summary:
        return cleaned
    if not cleaned:
        return summary
    return f"{cleaned}\n\n{summary}"


def image_attachment_paths(attachments: Any) -> list[str]:
    paths: list[str] = []
    for attachment in normalize_attachments(attachments):
        content_type = attachment.get("content_type") or ""
        path = Path(str(attachment.get("path") or ""))
        if content_type.startswith("image/") or path.suffix.lower() in IMAGE_SUFFIXES:
            if path.is_file():
                paths.append(str(path))
    return paths


class ChatUploadStore:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or chat_upload_dir()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.directory.chmod(0o700)

    def save(self, *, filename: str, content: bytes, content_type: str = "", ttl_seconds: int | None = None) -> ChatUpload:
        if len(content) > MAX_CHAT_UPLOAD_BYTES:
            raise ValueError("chat upload is too large")
        now = time.time()
        ttl = ttl_seconds or chat_upload_ttl_seconds()
        upload_id = f"upl_{uuid.uuid4().hex}"
        safe_name = self._safe_filename(filename)
        path = self.directory / f"{upload_id}_{safe_name}"
        path.write_bytes(content)
        path.chmod(0o600)
        resolved_type = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        return ChatUpload(
            upload_id=upload_id,
            filename=safe_name,
            path=str(path),
            size=len(content),
            content_type=resolved_type,
            created_at=now,
            expires_at=now + ttl,
        )

    def cleanup_expired(self, *, ttl_seconds: int | None = None, now: float | None = None) -> int:
        cutoff = (now or time.time()) - (ttl_seconds or chat_upload_ttl_seconds())
        removed = 0
        if not self.directory.exists():
            return 0
        for path in self.directory.iterdir():
            if not path.is_file():
                continue
            try:
                if path.stat().st_mtime <= cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        return removed

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = Path(filename or "upload.bin").name.strip() or "upload.bin"
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
        return safe[:160] or "upload.bin"

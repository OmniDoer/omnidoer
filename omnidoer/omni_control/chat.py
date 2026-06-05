"""Paired Control Client chat messages and streaming updates."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from omnidoer.omni_control.chat_uploads import append_attachments_to_text, normalize_attachments
from omnidoer.omni_control.state_io import atomic_write_json, locked_state_file
from omnidoer.paths import state_file


CHAT_ROLES = {"user", "assistant", "system"}
CHAT_STATUSES = {"queued", "claimed", "streaming", "completed", "cancelled"}
CHAT_RECORD_TYPES = {"message", "delta", "status", "tool_call", "tool_output", "error", "note", "terminal"}
MAX_CHAT_TEXT_LENGTH = 20000
MAX_CHAT_MESSAGES = 80
MAX_CHAT_RECORDS = 140
CHAT_RETENTION_SECONDS = 3 * 24 * 60 * 60
INTERRUPT_CLIENT_MESSAGE_PREFIXES = ("control_pause_", "omnidoer_pause_")
CLI_CLIENT_MESSAGE_PREFIX = "control_cli_"
PRIORITY_CLIENT_MESSAGE_PREFIXES = (*INTERRUPT_CLIENT_MESSAGE_PREFIXES, "control_continue_", CLI_CLIENT_MESSAGE_PREFIX)
_CLI_COMMAND_RE = re.compile(r"^/([A-Za-z][A-Za-z0-9-]*)(?:\s|$)")


def chat_cli_command_name(text: str) -> str | None:
    first_line = str(text or "").lstrip().splitlines()[0:1]
    if not first_line:
        return None
    match = _CLI_COMMAND_RE.match(first_line[0].strip())
    return match.group(1).lower() if match else None


def chat_text_is_cli_command(text: str) -> bool:
    return chat_cli_command_name(text) is not None


def chat_message_is_cli_command(message: "ChatMessage") -> bool:
    client_message_id = str(message.client_message_id or "")
    return client_message_id.startswith(CLI_CLIENT_MESSAGE_PREFIX) or chat_text_is_cli_command(message.text)


@dataclass
class ChatMessage:
    message_id: str
    sequence: int
    role: str
    text: str
    status: str = "completed"
    source: str = "control_client"
    author_device_id: str | None = None
    client_message_id: str | None = None
    reply_to_message_id: str | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    claimed_at: float | None = None
    completed_at: float | None = None

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["secret_fields_allowed"] = False
        data["control_client_calls_model"] = False
        data["submitted_to_openai_api_by_control_client"] = False
        data["delivered_to_agent"] = self.role != "user" or self.status in {"claimed", "completed"}
        return data


@dataclass
class ChatRecord:
    record_id: str
    sequence: int
    record_type: str
    text: str = ""
    role: str | None = None
    message_id: str | None = None
    source: str = "agent"
    data: dict[str, Any] | None = None
    created_at: float = 0.0

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["secret_fields_allowed"] = False
        payload["control_client_calls_model"] = False
        return payload


def control_message_priority(message: ChatMessage) -> int:
    client_message_id = str(message.client_message_id or "")
    if client_message_id.startswith(INTERRUPT_CLIENT_MESSAGE_PREFIXES):
        return 0
    if client_message_id.startswith(PRIORITY_CLIENT_MESSAGE_PREFIXES):
        return 1
    return 2


class ChatStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_chat_messages.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_payload(self) -> tuple[int, dict[str, ChatMessage], int, dict[str, ChatRecord]]:
        if not self.path.exists():
            return 1, {}, 1, {}
        raw = json.loads(self.path.read_text())
        if isinstance(raw, dict) and "messages" in raw:
            raw_messages = raw.get("messages") or {}
            next_sequence = int(raw.get("next_sequence") or 1)
            raw_records = raw.get("records") or {}
            next_record_sequence = int(raw.get("next_record_sequence") or 1)
        else:
            raw_messages = raw
            next_sequence = 1
            raw_records = {}
            next_record_sequence = 1
        messages = {key: ChatMessage(**value) for key, value in raw_messages.items()}
        records = {key: ChatRecord(**value) for key, value in raw_records.items()}
        if messages:
            next_sequence = max(next_sequence, max(message.sequence for message in messages.values()) + 1)
        if records:
            next_record_sequence = max(next_record_sequence, max(record.sequence for record in records.values()) + 1)
        return next_sequence, messages, next_record_sequence, records

    def _save(
        self,
        next_sequence: int,
        messages: dict[str, ChatMessage],
        next_record_sequence: int,
        records: dict[str, ChatRecord],
    ) -> None:
        messages, records = self._prune(messages, records)
        payload = {
            "next_sequence": next_sequence,
            "next_record_sequence": next_record_sequence,
            "messages": {key: asdict(value) for key, value in messages.items()},
            "records": {key: asdict(value) for key, value in records.items()},
        }
        atomic_write_json(self.path, payload)

    def _prune(
        self,
        messages: dict[str, ChatMessage],
        records: dict[str, ChatRecord],
    ) -> tuple[dict[str, ChatMessage], dict[str, ChatRecord]]:
        cutoff = time.time() - CHAT_RETENTION_SECONDS
        active_message_ids = {
            message.message_id
            for message in messages.values()
            if message.status in {"queued", "claimed", "streaming"}
        }
        messages = {
            key: value
            for key, value in messages.items()
            if key in active_message_ids or max(float(value.created_at or 0), float(value.updated_at or 0)) >= cutoff
        }
        records = {
            key: value
            for key, value in records.items()
            if (value.message_id and value.message_id in active_message_ids) or float(value.created_at or 0) >= cutoff
        }

        sorted_records = sorted(records.values(), key=lambda record: record.sequence)
        retained_records = sorted_records[-MAX_CHAT_RECORDS:]
        retained_record_ids = {record.record_id for record in retained_records}
        records = {key: value for key, value in records.items() if key in retained_record_ids}

        referenced_message_ids = {
            record.message_id
            for record in records.values()
            if record.message_id
        }
        recent_messages = sorted(messages.values(), key=lambda message: message.sequence)[-MAX_CHAT_MESSAGES:]
        retained_message_ids = active_message_ids | referenced_message_ids | {message.message_id for message in recent_messages}
        messages = {key: value for key, value in messages.items() if key in retained_message_ids}
        return messages, records

    def prune_now(self) -> None:
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            self._save(next_sequence, messages, next_record_sequence, records)

    def _new_record(
        self,
        next_record_sequence: int,
        *,
        record_type: str,
        text: str = "",
        role: str | None = None,
        message_id: str | None = None,
        source: str = "agent",
        data: dict[str, Any] | None = None,
    ) -> ChatRecord:
        if record_type not in CHAT_RECORD_TYPES:
            raise ValueError("invalid chat record type")
        if role is not None and role not in CHAT_ROLES:
            raise ValueError("invalid chat role")
        if len(text) > MAX_CHAT_TEXT_LENGTH:
            raise ValueError("chat text is too long")
        return ChatRecord(
            record_id=f"rec_{uuid.uuid4().hex}",
            sequence=next_record_sequence,
            record_type=record_type,
            text=text,
            role=role,
            message_id=message_id,
            source=source,
            data=data or {},
            created_at=time.time(),
        )

    def list(self, *, limit: int = 200, after_sequence: int | None = None) -> list[ChatMessage]:
        _, messages, _, _ = self._load_payload()
        items = sorted(messages.values(), key=lambda message: message.sequence)
        if after_sequence is not None:
            items = [message for message in items if message.sequence > after_sequence]
        return items[-max(1, min(limit, 1000)) :]

    def list_records(self, *, limit: int = 140, after_sequence: int | None = None) -> list[ChatRecord]:
        _, _, _, records = self._load_payload()
        items = sorted(records.values(), key=lambda record: record.sequence)
        if after_sequence is not None:
            items = [record for record in items if record.sequence > after_sequence]
        return items[-max(1, min(limit, MAX_CHAT_RECORDS)) :]

    def get(self, message_id: str) -> ChatMessage:
        _, messages, _, _ = self._load_payload()
        try:
            return messages[message_id]
        except KeyError as exc:
            raise KeyError(f"chat message not found: {message_id}") from exc

    def append(
        self,
        *,
        role: str,
        text: str,
        status: str | None = None,
        source: str = "control_client",
        author_device_id: str | None = None,
        client_message_id: str | None = None,
        reply_to_message_id: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        normalized_attachments = normalize_attachments(attachments)
        cleaned = append_attachments_to_text(text, normalized_attachments) if role == "user" else text
        if role not in CHAT_ROLES:
            raise ValueError("invalid chat role")
        if (status or "completed") not in CHAT_STATUSES:
            raise ValueError("invalid chat status")
        if role == "user" and not cleaned:
            raise ValueError("chat text is required")
        if len(cleaned) > MAX_CHAT_TEXT_LENGTH:
            raise ValueError("chat text is too long")
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            now = time.time()
            resolved_status = status or ("queued" if role == "user" else "completed")
            message = ChatMessage(
                message_id=f"msg_{uuid.uuid4().hex}",
                sequence=next_sequence,
                role=role,
                text=cleaned,
                status=resolved_status,
                source=source,
                author_device_id=author_device_id,
                client_message_id=client_message_id,
                reply_to_message_id=reply_to_message_id,
                attachments=normalized_attachments,
                created_at=now,
                updated_at=now,
                completed_at=now if resolved_status == "completed" else None,
            )
            messages[message.message_id] = message
            record = self._new_record(
                next_record_sequence,
                record_type="message",
                text=message.text,
                role=message.role,
                message_id=message.message_id,
                source=source,
                data={"status": message.status, "attachments": normalized_attachments},
            )
            records[record.record_id] = record
            self._save(next_sequence + 1, messages, next_record_sequence + 1, records)
            return message

    def next_user_message(self, *, claim: bool = True) -> ChatMessage | None:
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            pending = sorted(
                (message for message in messages.values() if message.role == "user" and message.status == "queued"),
                key=lambda message: (control_message_priority(message), message.sequence),
            )
            if not pending:
                return None
            message = pending[0]
            if claim:
                now = time.time()
                message.status = "claimed"
                message.claimed_at = now
                message.updated_at = now
                messages[message.message_id] = message
                record = self._new_record(
                    next_record_sequence,
                    record_type="status",
                    text="User message delivered to local agent.",
                    role="system",
                    message_id=message.message_id,
                    source="control_service",
                    data={"status": message.status},
                )
                records[record.record_id] = record
                self._save(next_sequence, messages, next_record_sequence + 1, records)
            return message

    def append_delta(self, message_id: str, delta: str) -> ChatMessage:
        if not delta:
            return self.get(message_id)
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            message = messages[message_id]
            if message.role != "assistant":
                raise ValueError("only assistant messages can stream")
            if message.status not in {"streaming", "claimed"}:
                raise ValueError("message is not streaming")
            if len(message.text) + len(delta) > MAX_CHAT_TEXT_LENGTH:
                raise ValueError("chat text is too long")
            message.text += delta
            message.status = "streaming"
            message.updated_at = time.time()
            messages[message.message_id] = message
            record = self._new_record(
                next_record_sequence,
                record_type="delta",
                text=delta,
                role="assistant",
                message_id=message.message_id,
                source=message.source,
                data={"status": message.status},
            )
            records[record.record_id] = record
            self._save(next_sequence, messages, next_record_sequence + 1, records)
            return message

    def complete(self, message_id: str, *, text: str | None = None) -> ChatMessage:
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            message = messages[message_id]
            if text is not None:
                if len(text) > MAX_CHAT_TEXT_LENGTH:
                    raise ValueError("chat text is too long")
                message.text = text
            now = time.time()
            message.status = "completed"
            message.updated_at = now
            message.completed_at = now
            messages[message.message_id] = message
            role_label = "Assistant" if message.role == "assistant" else "User"
            record = self._new_record(
                next_record_sequence,
                record_type="status",
                text=f"{role_label} message completed.",
                role="system",
                message_id=message.message_id,
                source="control_service",
                data={"status": message.status},
            )
            records[record.record_id] = record
            self._save(next_sequence, messages, next_record_sequence + 1, records)
            return message

    def cancel(self, message_id: str) -> ChatMessage:
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            message = messages[message_id]
            message.status = "cancelled"
            message.updated_at = time.time()
            messages[message.message_id] = message
            record = self._new_record(
                next_record_sequence,
                record_type="status",
                text="Chat message cancelled.",
                role="system",
                message_id=message.message_id,
                source="control_service",
                data={"status": message.status},
            )
            records[record.record_id] = record
            self._save(next_sequence, messages, next_record_sequence + 1, records)
            return message

    def append_record(
        self,
        *,
        record_type: str,
        text: str = "",
        role: str | None = None,
        message_id: str | None = None,
        source: str = "agent",
        data: dict[str, Any] | None = None,
    ) -> ChatRecord:
        with locked_state_file(self.path):
            next_sequence, messages, next_record_sequence, records = self._load_payload()
            record = self._new_record(
                next_record_sequence,
                record_type=record_type,
                text=text,
                role=role,
                message_id=message_id,
                source=source,
                data=data,
            )
            records[record.record_id] = record
            self._save(next_sequence, messages, next_record_sequence + 1, records)
            return record

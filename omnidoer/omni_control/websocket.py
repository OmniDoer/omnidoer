"""WebSocket/SSE push contract for Cloud Direct mode."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any


WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEVICE_AUTH_SUBPROTOCOL_PREFIX = "omnidoer-v1."


def sse_event(event: str, payload: dict) -> bytes:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"event: {event}\ndata: {data}\n\n".encode()


def websocket_origin_allowed(origin: str | None, allowed_origin: str) -> bool:
    return bool(origin) and origin == allowed_origin


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def websocket_accept_key(client_key: str) -> str:
    digest = hashlib.sha1(f"{client_key}{WEBSOCKET_GUID}".encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def websocket_text_frame(payload: dict[str, Any]) -> bytes:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    length = len(data)
    if length < 126:
        header = bytes([0x81, length])
    elif length < 65536:
        header = bytes([0x81, 126, (length >> 8) & 0xFF, length & 0xFF])
    else:
        header = bytes(
            [
                0x81,
                127,
                (length >> 56) & 0xFF,
                (length >> 48) & 0xFF,
                (length >> 40) & 0xFF,
                (length >> 32) & 0xFF,
                (length >> 24) & 0xFF,
                (length >> 16) & 0xFF,
                (length >> 8) & 0xFF,
                length & 0xFF,
            ]
        )
    return header + data


def encode_device_auth_subprotocol(
    *,
    device_id: str,
    timestamp: str,
    nonce: str,
    signature: str,
    session_id: str = "",
) -> str:
    payload_data = {"device_id": device_id, "timestamp": timestamp, "nonce": nonce, "signature": signature}
    if session_id:
        payload_data["session_id"] = session_id
    payload = json.dumps(payload_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{DEVICE_AUTH_SUBPROTOCOL_PREFIX}{_b64url(payload)}"


def decode_device_auth_subprotocol(header: str | None) -> dict[str, str] | None:
    if not header:
        return None
    for candidate in [part.strip() for part in header.split(",")]:
        if not candidate.startswith(DEVICE_AUTH_SUBPROTOCOL_PREFIX):
            continue
        raw = _unb64url(candidate.removeprefix(DEVICE_AUTH_SUBPROTOCOL_PREFIX))
        payload = json.loads(raw.decode("utf-8"))
        decoded = {
            "device_id": str(payload.get("device_id") or ""),
            "timestamp": str(payload.get("timestamp") or ""),
            "nonce": str(payload.get("nonce") or ""),
            "signature": str(payload.get("signature") or ""),
            "subprotocol": candidate,
        }
        if payload.get("session_id"):
            decoded["session_id"] = str(payload.get("session_id") or "")
        return decoded
    return None

"""Paired Control Client device identities."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from omnidoer.omni_control.state_io import atomic_write_json, locked_state_file
from omnidoer.paths import state_file


@dataclass
class Device:
    device_id: str
    name: str
    public_key: str
    fingerprint: str
    revoked: bool = False
    created_at: float = field(default_factory=time.time)
    last_seen_at: float | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "fingerprint": self.fingerprint,
            "revoked": self.revoked,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
        }


class DeviceStore:
    def __init__(self, path: Path | None = None):
        self.path = path or state_file("control_devices.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Device]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        return {key: Device(**value) for key, value in raw.items()}

    def _save(self, devices: dict[str, Device]) -> None:
        atomic_write_json(self.path, {key: asdict(value) for key, value in devices.items()})

    def register(self, *, name: str, public_key: str) -> Device:
        with locked_state_file(self.path):
            fingerprint = hashlib.sha256(public_key.encode()).hexdigest()[:32]
            device = Device(
                device_id=f"dev_{uuid.uuid4().hex}",
                name=name.strip() or "Control Client",
                public_key=public_key,
                fingerprint=":".join(fingerprint[i : i + 2] for i in range(0, len(fingerprint), 2)),
            )
            devices = self._load()
            devices[device.device_id] = device
            self._save(devices)
            return device

    def get(self, device_id: str) -> Device:
        devices = self._load()
        try:
            return devices[device_id]
        except KeyError as exc:
            raise KeyError(f"device not found: {device_id}") from exc

    def list(self) -> list[Device]:
        return sorted(self._load().values(), key=lambda item: item.created_at)

    def revoke(self, device_id: str) -> Device:
        with locked_state_file(self.path):
            devices = self._load()
            device = devices[device_id]
            device.revoked = True
            devices[device_id] = device
            self._save(devices)
            return device

    def touch(self, device_id: str) -> Device:
        with locked_state_file(self.path):
            devices = self._load()
            device = devices[device_id]
            if device.revoked:
                raise PermissionError("device revoked")
            device.last_seen_at = time.time()
            devices[device_id] = device
            self._save(devices)
            return device

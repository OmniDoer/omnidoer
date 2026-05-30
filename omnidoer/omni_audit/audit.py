"""Hash-chained audit log with redaction."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from omnidoer.omni_observer import redact_dom_snapshot
from omnidoer.paths import default_audit_path


GENESIS = "0" * 64


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = path or default_audit_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, event_type: str, **fields: Any) -> dict[str, Any]:
        previous_hash = self._events()[-1]["event_hash"] if self.path.exists() and self._events() else GENESIS
        event = redact_dom_snapshot(
            {
                "timestamp": time.time(),
                "event_type": event_type,
                "previous_hash": previous_hash,
                **fields,
            }
        )
        event_without_hash = json.dumps(event, sort_keys=True, separators=(",", ":"))
        event["event_hash"] = hashlib.sha256(event_without_hash.encode()).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event

    def tail(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._events()[-limit:]

    def verify(self) -> bool:
        previous = GENESIS
        for event in self._events():
            event_hash = event.get("event_hash")
            body = dict(event)
            body.pop("event_hash", None)
            if body.get("previous_hash") != previous:
                return False
            expected = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if expected != event_hash:
                return False
            previous = event_hash
        return True


def handle_audit_command(args) -> int:
    audit = AuditLog()
    if args.audit_command == "tail":
        print(json.dumps(audit.tail(), indent=2, sort_keys=True))
        return 0
    if args.audit_command == "verify":
        ok = audit.verify()
        print("audit verify: ok" if ok else "audit verify: failed")
        return 0 if ok else 1
    return 0

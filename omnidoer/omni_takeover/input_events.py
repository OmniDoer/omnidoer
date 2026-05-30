"""User input event parser for takeover test mode."""

from __future__ import annotations

from omnidoer.omni_takeover.models import InputEvent


def parse_actions(raw: str) -> list[InputEvent]:
    events: list[InputEvent] = []
    for part in filter(None, (item.strip() for item in raw.split(";"))):
        if part.startswith("tap:"):
            x_raw, y_raw = part.removeprefix("tap:").split(",", 1)
            events.append(InputEvent("tap", x=int(x_raw), y=int(y_raw)))
        elif part.startswith("scroll:"):
            events.append(InputEvent("scroll", delta_y=int(part.removeprefix("scroll:"))))
        elif part.startswith("type:"):
            events.append(InputEvent("type", text=part.removeprefix("type:")))
        elif part == "release":
            events.append(InputEvent("release"))
    return events

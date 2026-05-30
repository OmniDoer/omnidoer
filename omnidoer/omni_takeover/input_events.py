"""User input event parser for takeover test mode."""

from __future__ import annotations

from omnidoer.omni_takeover.models import InputEvent


def event_from_dict(data: dict) -> InputEvent:
    return InputEvent(
        event_type=str(data.get("event_type") or data.get("type") or ""),
        x=data.get("x"),
        y=data.get("y"),
        to_x=data.get("to_x"),
        to_y=data.get("to_y"),
        text=data.get("text"),
        key=data.get("key"),
        delta_x=data.get("delta_x"),
        delta_y=data.get("delta_y"),
    )


def parse_actions(raw: str) -> list[InputEvent]:
    events: list[InputEvent] = []
    for part in filter(None, (item.strip() for item in raw.split(";"))):
        if part.startswith("tap:"):
            x_raw, y_raw = part.removeprefix("tap:").split(",", 1)
            events.append(InputEvent("tap", x=int(x_raw), y=int(y_raw)))
        elif part.startswith("click:"):
            x_raw, y_raw = part.removeprefix("click:").split(",", 1)
            events.append(InputEvent("click", x=int(x_raw), y=int(y_raw)))
        elif part.startswith("double_click:"):
            x_raw, y_raw = part.removeprefix("double_click:").split(",", 1)
            events.append(InputEvent("double_click", x=int(x_raw), y=int(y_raw)))
        elif part.startswith("long_press:"):
            x_raw, y_raw = part.removeprefix("long_press:").split(",", 1)
            events.append(InputEvent("long_press", x=int(x_raw), y=int(y_raw)))
        elif part.startswith("drag:"):
            start, end = part.removeprefix("drag:").split("->", 1)
            x_raw, y_raw = start.split(",", 1)
            to_x_raw, to_y_raw = end.split(",", 1)
            events.append(InputEvent("drag", x=int(x_raw), y=int(y_raw), to_x=int(to_x_raw), to_y=int(to_y_raw)))
        elif part.startswith("scroll:"):
            events.append(InputEvent("scroll", delta_y=int(part.removeprefix("scroll:"))))
        elif part.startswith("type:"):
            events.append(InputEvent("type", text=part.removeprefix("type:")))
        elif part.startswith("key:"):
            events.append(InputEvent("key", key=part.removeprefix("key:")))
        elif part == "release":
            events.append(InputEvent("release"))
    return events

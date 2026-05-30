"""User input event parser for takeover test mode."""

from __future__ import annotations

from omnidoer.omni_takeover.models import InputEvent


ALLOWED_INPUT_EVENT_TYPES = {
    "tap",
    "click",
    "double_click",
    "long_press",
    "drag",
    "scroll",
    "type",
    "key",
    "release",
}
MAX_TAKEOVER_TEXT_CHARS = 4096
MAX_TAKEOVER_KEY_CHARS = 64


def _event_type(value: object) -> str:
    return str(value or "").strip()


def validate_input_event(event: InputEvent) -> None:
    """Validate control-only browser input without echoing user-provided text."""

    if event.event_type not in ALLOWED_INPUT_EVENT_TYPES:
        raise ValueError("unsupported takeover event")
    if event.text is not None and len(event.text) > MAX_TAKEOVER_TEXT_CHARS:
        raise ValueError("takeover text too long")
    if event.key is not None and len(event.key) > MAX_TAKEOVER_KEY_CHARS:
        raise ValueError("takeover key too long")


def event_from_dict(data: dict) -> InputEvent:
    event = InputEvent(
        event_type=_event_type(data.get("event_type") or data.get("type")),
        x=data.get("x"),
        y=data.get("y"),
        to_x=data.get("to_x"),
        to_y=data.get("to_y"),
        text=data.get("text"),
        key=data.get("key"),
        delta_x=data.get("delta_x"),
        delta_y=data.get("delta_y"),
    )
    validate_input_event(event)
    return event


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

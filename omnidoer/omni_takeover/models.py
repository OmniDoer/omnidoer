"""Takeover models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputEvent:
    event_type: str
    x: int | None = None
    y: int | None = None
    text: str | None = None
    delta_y: int | None = None

"""Form inspection helpers."""

from __future__ import annotations

from urllib.parse import urljoin


def resolve_form_action(page_url: str, action: str | None) -> str:
    return urljoin(page_url, action or page_url)

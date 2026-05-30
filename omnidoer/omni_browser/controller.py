"""Headless Chromium controller.

Playwright is optional at import time so non-browser safety tests can run on
minimal systems. Browser commands explain how to install it when unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from omnidoer.omni_challenge.detector import detect_challenge_from_url
from omnidoer.omni_observer import redact_dom_snapshot, redact_text
from omnidoer.omni_observer.redactor import SECRET_FIELD_RE
from omnidoer.omni_policy.policy import origin_from_url
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.stream import frame_from_png


class BrowserUnavailable(RuntimeError):
    pass


class BrowserController:
    def __init__(self, headless: bool = True, downloads_path: str | None = None):
        self.headless = headless
        self.downloads_path = downloads_path
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self) -> "BrowserController":
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise BrowserUnavailable(
                "Playwright is not installed. Run python3 -m pip install -e '.[dev]' and python3 -m playwright install chromium."
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(accept_downloads=True)
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    @property
    def page(self):
        if self._page is None:
            raise BrowserUnavailable("browser is not started")
        return self._page

    def open(self, url: str) -> dict:
        self.page.goto(url, wait_until="domcontentloaded")
        return {"status": "opened", "url": self.current_url(), "secret_exposed_to_model": False}

    def current_url(self) -> str:
        return self.page.url

    def current_origin(self) -> str | None:
        return origin_from_url(self.current_url())

    def observe_dom(self) -> dict:
        data = self.page.evaluate(
            """() => Array.from(document.querySelectorAll('input, textarea, button, a, h1, h2, p')).map((el) => ({
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || '',
                name: el.getAttribute('name') || '',
                id: el.getAttribute('id') || '',
                autocomplete: el.getAttribute('autocomplete') || '',
                placeholder: el.getAttribute('placeholder') || '',
                aria_label: el.getAttribute('aria-label') || '',
                text: el.innerText || el.getAttribute('value') || '',
                value: el.matches('input, textarea') ? el.value : '',
                href: el.getAttribute('href') || ''
            }))"""
        )
        return {"url": self.current_url(), "origin": self.current_origin(), "nodes": redact_dom_snapshot(data)}

    def observe_accessibility(self) -> dict:
        accessibility = getattr(self.page, "accessibility", None)
        if accessibility is not None:
            try:
                snapshot = accessibility.snapshot() or {}
                return redact_dom_snapshot(snapshot)
            except Exception:
                pass
        snapshot = self.page.evaluate(
            """() => ({
                role: 'document',
                name: document.title || '',
                children: Array.from(document.querySelectorAll('label, input, textarea, button, a, h1, h2, p')).map((el) => ({
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    type: el.getAttribute('type') || '',
                    name: el.getAttribute('name') || el.getAttribute('aria-label') || el.innerText || '',
                    id: el.getAttribute('id') || '',
                    label: el.labels && el.labels.length ? Array.from(el.labels).map((label) => label.innerText).join(' ') : '',
                    autocomplete: el.getAttribute('autocomplete') || '',
                    description: el.getAttribute('placeholder') || '',
                    value: el.matches('input, textarea') ? el.value : ''
                }))
            })"""
        )
        return redact_dom_snapshot(snapshot)

    def screenshot(self) -> bytes:
        return self.page.screenshot(full_page=False)

    def takeover_frame(self) -> dict:
        viewport = self.page.viewport_size or {"width": 1280, "height": 720}
        return frame_from_png(
            self.screenshot(),
            url=self.current_url(),
            origin=self.current_origin() or "",
            viewport_width=int(viewport["width"]),
            viewport_height=int(viewport["height"]),
        )

    def click(self, selector: str) -> dict:
        self.page.click(selector)
        return {"status": "clicked", "secret_exposed_to_model": False}

    def type_text(self, selector: str, text: str) -> dict:
        if self._selector_targets_sensitive_field(selector):
            return {
                "status": "rejected",
                "reason": "sensitive fields require Secret Broker or Challenge Relay",
                "secret_exposed_to_model": False,
            }
        self.page.fill(selector, text)
        return {"status": "typed", "secret_exposed_to_model": False}

    def select(self, selector: str, value: str) -> dict:
        if self._selector_targets_sensitive_field(selector):
            return {
                "status": "rejected",
                "reason": "sensitive fields require Secret Broker or Challenge Relay",
                "secret_exposed_to_model": False,
            }
        self.page.select_option(selector, value=value)
        return {"status": "selected", "secret_exposed_to_model": False}

    def upload_file(self, selector: str, file_path: str | Path) -> dict:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        self.page.set_input_files(selector, str(path))
        return {"status": "uploaded", "filename": path.name, "secret_exposed_to_model": False}

    def fill_field(self, selector: str, value: str, *, secret: bool = False) -> dict:
        self.page.fill(selector, value)
        return {"status": "filled", "secret": bool(secret), "secret_exposed_to_model": False}

    def _selector_targets_sensitive_field(self, selector: str) -> bool:
        try:
            metadata = self.page.locator(selector).first.evaluate(
                """(el) => ({
                    type: el.getAttribute('type') || '',
                    name: el.getAttribute('name') || '',
                    id: el.getAttribute('id') || '',
                    autocomplete: el.getAttribute('autocomplete') || '',
                    placeholder: el.getAttribute('placeholder') || '',
                    aria_label: el.getAttribute('aria-label') || ''
                })"""
            )
        except Exception:
            return False
        haystack = " ".join(str(value) for value in metadata.values())
        return bool(SECRET_FIELD_RE.search(haystack))

    def apply_user_input_event(self, event: InputEvent) -> dict:
        if event.event_type in {"tap", "click"}:
            if event.x is None or event.y is None:
                raise ValueError("tap/click requires x and y")
            self.page.mouse.click(event.x, event.y)
        elif event.event_type == "double_click":
            if event.x is None or event.y is None:
                raise ValueError("double_click requires x and y")
            self.page.mouse.dblclick(event.x, event.y)
        elif event.event_type == "long_press":
            if event.x is None or event.y is None:
                raise ValueError("long_press requires x and y")
            self.page.mouse.move(event.x, event.y)
            self.page.mouse.down()
            self.page.wait_for_timeout(650)
            self.page.mouse.up()
        elif event.event_type == "drag":
            if event.x is None or event.y is None or event.to_x is None or event.to_y is None:
                raise ValueError("drag requires x, y, to_x and to_y")
            self.page.mouse.move(event.x, event.y)
            self.page.mouse.down()
            self.page.mouse.move(event.to_x, event.to_y, steps=10)
            self.page.mouse.up()
        elif event.event_type == "scroll":
            self.page.mouse.wheel(event.delta_x or 0, event.delta_y or 0)
        elif event.event_type == "type":
            self.page.keyboard.type(event.text or "")
        elif event.event_type == "key":
            self.page.keyboard.press(event.key or "Enter")
        else:
            raise ValueError(f"unsupported takeover event: {event.event_type}")
        return {"status": "event_applied", "secret_exposed_to_model": False}

    def inspect_forms(self) -> list[dict[str, Any]]:
        return self.page.evaluate(
            """() => Array.from(document.forms).map((form) => ({
                action: form.action,
                method: form.method,
                fields: Array.from(form.elements).map((el) => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.getAttribute('type') || '',
                    name: el.getAttribute('name') || '',
                    id: el.getAttribute('id') || ''
                }))
            }))"""
        )

    def inspect_frame_tree(self) -> dict:
        return {"top_level_url": self.current_url(), "frames": [frame.url for frame in self.page.frames]}

    def inspect_form_action(self) -> str | None:
        forms = self.inspect_forms()
        return forms[0]["action"] if forms else None

    def detect_challenge(self) -> str | None:
        return detect_challenge_from_url(self.current_url())

    def detect_antibot(self) -> bool:
        return "antibot" in self.current_url().lower()

    def download_current_file(self, selector: str = "a[download]", output_dir: str | None = None) -> Path:
        output = Path(output_dir or self.downloads_path or ".omnidoer/downloads")
        output.mkdir(parents=True, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.page.click(selector)
        download = download_info.value
        path = output / download.suggested_filename
        download.save_as(path)
        return path

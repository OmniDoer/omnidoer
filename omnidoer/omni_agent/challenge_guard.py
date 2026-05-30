"""Challenge routing guard for browser-driven agent tasks."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Protocol

from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_challenge.relay import ChallengeRelay, complete_in_test_mode as complete_challenge
from omnidoer.omni_challenge.relay import request_user_interaction
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard
from omnidoer.omni_takeover.input_events import parse_actions
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.relay import apply_input_event, release_control, request_user_control, start_stream


class GuardBrowser(Protocol):
    def current_url(self) -> str: ...
    def detect_antibot(self) -> bool: ...
    def detect_challenge(self) -> str | None: ...
    def click(self, selector: str) -> dict: ...
    def takeover_frame(self) -> dict: ...
    def apply_user_input_event(self, event: InputEvent) -> dict: ...
    def fill_field(self, selector: str, value: str, *, secret: bool = False) -> dict: ...
    def press_key(self, key: str) -> dict: ...


CODE_CHALLENGE_FIELDS = {
    "totp": ["otp"],
    "sms": ["code"],
    "email": ["code"],
    "one_time_code": ["code"],
    "3ds": ["code"],
}

TAKEOVER_CHALLENGES = {
    "antibot",
    "captcha",
    "passkey",
    "webauthn",
    "device_confirmation",
}

TEST_VALUE_ENV = {
    "totp": "OMNIDOER_TEST_SMS_CODE",
    "sms": "OMNIDOER_TEST_SMS_CODE",
    "email": "OMNIDOER_TEST_EMAIL_CODE",
    "one_time_code": "OMNIDOER_TEST_SMS_CODE",
    "3ds": "OMNIDOER_TEST_SMS_CODE",
}

TEST_VALUE_DEFAULT = {
    "totp": "123456",
    "sms": "123456",
    "email": "654321",
    "one_time_code": "123456",
    "3ds": "123456",
}

TAKEOVER_FOCUS_SELECTOR = {
    "antibot": "#takeover",
    "captcha": "#ack",
    "passkey": "#passkey",
    "webauthn": "#passkey",
    "device_confirmation": "#passkey",
}


@dataclass(frozen=True)
class ChallengeResolution:
    status: str
    mode: str
    challenge_type: str | None = None
    request_id: str | None = None
    agent_resumed: bool = False
    secret_exposed_to_model: bool = False

    def to_public_dict(self) -> dict:
        return {
            "status": self.status,
            "mode": self.mode,
            "challenge_type": self.challenge_type,
            "request_id": self.request_id,
            "agent_resumed": self.agent_resumed,
            "secret_exposed_to_model": False,
        }


def resolve_current_browser_challenge(
    *,
    origin: str,
    browser: GuardBrowser,
    browser_context_id: str,
    reason: str | None = None,
    store: RequestStore | None = None,
    timeout_seconds: int = 300,
    auto_submit: bool = True,
) -> ChallengeResolution:
    """Route the current page through challenge relay or human takeover.

    This is the transition point between autonomous browser action and
    user-controlled action. It intentionally returns status only; user-entered
    codes, passwords, passkey material, and takeover text never appear in the
    returned payload.
    """

    store = store or RequestStore()
    top_level_url = browser.current_url()
    challenge_type = "antibot" if browser.detect_antibot() else browser.detect_challenge()
    if challenge_type is None:
        return ChallengeResolution(status="no_challenge", mode="agent")
    if challenge_type in TAKEOVER_CHALLENGES:
        return _route_takeover(
            origin=origin,
            top_level_url=top_level_url,
            challenge_type=challenge_type,
            browser=browser,
            browser_context_id=browser_context_id,
            reason=reason or f"{challenge_type} requires user takeover",
            store=store,
            timeout_seconds=timeout_seconds,
        )
    return _route_code_challenge(
        origin=origin,
        top_level_url=top_level_url,
        challenge_type=challenge_type,
        browser=browser,
        reason=reason or f"{challenge_type} requires user completion",
        store=store,
        timeout_seconds=timeout_seconds,
        auto_submit=auto_submit,
    )


def _route_code_challenge(
    *,
    origin: str,
    top_level_url: str,
    challenge_type: str,
    browser: GuardBrowser,
    reason: str,
    store: RequestStore,
    timeout_seconds: int,
    auto_submit: bool,
) -> ChallengeResolution:
    fields = CODE_CHALLENGE_FIELDS.get(challenge_type, ["code"])
    request = request_user_interaction(
        origin=origin,
        top_level_url=top_level_url,
        challenge_type=challenge_type,
        reason=reason,
        fields=fields,
        risk_level="medium",
        store=store,
    )
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") == "1":
        value = _test_value(challenge_type)
        browser.fill_field(_selector_for_fields(fields), value, secret=True)
        if auto_submit:
            _submit_current_form(browser)
        complete_challenge(request.request_id, store=store)
    else:
        _wait_for_ciphertext(store, request.request_id, timeout_seconds=timeout_seconds)
        relay = ChallengeRelay(store=store, replay_guard=ReplayGuard())
        relay.inject_response_if_applicable(request.request_id, browser_controller=browser)
        if auto_submit:
            _submit_current_form(browser)
    AuditLog().append(
        "agent_resumed_after_challenge",
        request_id=request.request_id,
        origin=origin,
        challenge_type=challenge_type,
        status="ok",
    )
    return ChallengeResolution(
        status="challenge_completed",
        mode="challenge_relay",
        challenge_type=challenge_type,
        request_id=request.request_id,
        agent_resumed=True,
    )


def _route_takeover(
    *,
    origin: str,
    top_level_url: str,
    challenge_type: str,
    browser: GuardBrowser,
    browser_context_id: str,
    reason: str,
    store: RequestStore,
    timeout_seconds: int,
) -> ChallengeResolution:
    request = request_user_control(
        origin=origin,
        top_level_url=top_level_url,
        reason=reason,
        browser_context_id=browser_context_id,
        risk_level="high",
        store=store,
    )
    start_stream(request.request_id, browser_controller=browser, store=store)
    if os.environ.get("OMNIDOER_TAKEOVER_TEST_MODE") == "1":
        focus_selector = TAKEOVER_FOCUS_SELECTOR.get(challenge_type)
        for event in parse_actions(os.environ.get("OMNIDOER_TEST_TAKEOVER_ACTIONS", "release")):
            if event.event_type == "release":
                break
            if focus_selector and event.event_type == "type":
                browser.fill_field(focus_selector, "", secret=True)
            apply_input_event(request.request_id, event, browser_controller=browser, store=store)
        if focus_selector:
            _submit_current_form(browser)
        release_control(request.request_id, store=store)
    else:
        _wait_for_release(store, request.request_id, timeout_seconds=timeout_seconds)
    AuditLog().append(
        "agent_resumed_after_takeover",
        request_id=request.request_id,
        origin=origin,
        challenge_type=challenge_type,
        status="ok",
    )
    return ChallengeResolution(
        status="user_completed_takeover",
        mode="human_takeover",
        challenge_type=challenge_type,
        request_id=request.request_id,
        agent_resumed=True,
    )


def _selector_for_fields(fields: list[str]) -> str:
    selectors: list[str] = []
    for field in fields:
        selectors.extend([f"#{field}", f"input[name='{field}']"])
    return ", ".join(selectors)


def _test_value(challenge_type: str) -> str:
    env_name = TEST_VALUE_ENV.get(challenge_type, "OMNIDOER_TEST_SMS_CODE")
    return os.environ.get(env_name, TEST_VALUE_DEFAULT.get(challenge_type, "123456"))


def _submit_current_form(browser: GuardBrowser) -> None:
    try:
        browser.click("button[type='submit']")
    except Exception:
        browser.press_key("Enter")


def _wait_for_ciphertext(store: RequestStore, request_id: str, *, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if store.get(request_id).response_ciphertext is not None:
            return
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for Control Client challenge response")


def _wait_for_release(store: RequestStore, request_id: str, *, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if store.get(request_id).status == "released":
            return
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for Control Client release")

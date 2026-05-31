"""Rule-based local demo agent used for OmniDoer MVP E2E tests.

This module does not call any model provider or OpenAI API. It is a deterministic
demo runner that exercises Broker, Vault, Control Requests, Challenge Relay,
Human Takeover Relay, Approval Gate, and Audit Log against the local mock site.
"""

from __future__ import annotations

import os
import time
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from omnidoer.omni_approval.approval import decide, request_approval
from omnidoer.omni_agent.challenge_guard import resolve_current_browser_challenge
from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_broker.broker import should_save_to_vault
from omnidoer.omni_challenge.relay import complete_in_test_mode as complete_challenge
from omnidoer.omni_challenge.relay import request_user_interaction
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import decrypt_control_envelope, encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_takeover.browser_worker import BrowserContextWorker
from omnidoer.omni_takeover.input_events import parse_actions
from omnidoer.omni_takeover.models import InputEvent
from omnidoer.omni_takeover.relay import apply_input_event, release_control, request_registration_handoff, request_user_control, start_stream
from omnidoer.omni_takeover.sessions import registered_browser_context
from omnidoer.omni_vault.models import CredentialSecret
from omnidoer.omni_vault.vault import Vault, _passphrase_from_source


ABORTED_REQUEST_STATUSES = {"denied", "expired", "cancelled", "rejected", "failed"}


class DemoHttpClient:
    def __init__(self, origin: str):
        self.origin = origin.rstrip("/")
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def get(self, path: str) -> str:
        return self.opener.open(self.origin + path, timeout=10).read().decode("utf-8", "replace")

    def post(self, path: str, data: dict[str, str]) -> str:
        encoded = urlencode(data).encode()
        request = Request(self.origin + path, data=encoded, method="POST")
        return self.opener.open(request, timeout=10).read().decode("utf-8", "replace")

    def download(self, path: str, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.opener.open(self.origin + path, timeout=10).read())
        return output


def _vault(args) -> Vault:
    return Vault.load(args.vault, _passphrase_from_source(args.passphrase_env, getattr(args, "passphrase_file", None)))


def _decrypt_request_payload(request) -> dict:
    expected_expires_at = request.expires_at if request.response_ciphertext.get("expires_at") is not None else None
    return decrypt_control_envelope(
        request.response_ciphertext,
        request_id=request.request_id,
        origin=request.origin,
        request_type=request.request_type,
        device_id=request.allowed_device_id,
        expires_at=expected_expires_at,
    )


def _wait_for_request_payload(request_id: str, timeout_seconds: int = 300) -> dict:
    store = RequestStore()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = store.get(request_id)
        if request.response_ciphertext:
            return _decrypt_request_payload(request)
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for Control Client request")


def _wait_for_challenge_payload(request_id: str, timeout_seconds: int = 300) -> dict:
    store = RequestStore()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = store.get(request_id)
        if request.response_ciphertext:
            payload = _decrypt_request_payload(request)
            if request.status != "challenge_completed":
                request = store.mark_challenge_completed(request_id)
            fields = [field for field in ("code", "otp", "ack") if payload.get(field)]
            AuditLog().append(
                "challenge_response_received",
                request_id=request_id,
                origin=request.origin,
                challenge_type=request.challenge_type,
                fields=fields,
                status="ok",
            )
            return payload
        if request.status in ABORTED_REQUEST_STATUSES:
            AuditLog().append("agent_challenge_wait_aborted", request_id=request_id, status=request.status)
            raise RuntimeError(f"Control Client challenge request ended: {request.status}")
        time.sleep(0.5)
    AuditLog().append("agent_challenge_wait_timeout", request_id=request_id, status="timeout")
    raise TimeoutError("timed out waiting for Control Client challenge response")


def _challenge_code_from_payload(payload: dict) -> str:
    value = payload.get("code") or payload.get("otp")
    if not value:
        raise ValueError("challenge payload has no code")
    return str(value)


def _credential_from_control_or_vault(args, origin: str) -> tuple[str, CredentialSecret]:
    vault = _vault(args)
    existing = vault.find_for_origin(origin)
    if existing:
        metadata = existing[0]
        return metadata.credential_id, vault.decrypt_credential(metadata.credential_id)

    keypair = load_or_create_keypair()
    request = RequestStore().create(
        "credential",
        origin=origin,
        top_level_url=f"{origin}/login",
        action_summary="Login to local demo site",
        risk_level="low",
        broker_public_key_fingerprint=keypair.fingerprint,
        requested_fields=["username", "password", "totp_seed"],
        save_to_vault=True,
    )
    print(f"created credential request {request.request_id}; use OmniDoer Control Client")

    if os.environ.get("OMNIDOER_CONTROL_TEST_MODE") == "1":
        payload = {
            "username": os.environ.get("OMNIDOER_TEST_USERNAME", "demo"),
            "password": os.environ.get("OMNIDOER_TEST_PASSWORD", ""),
            "totp_seed": os.environ.get("OMNIDOER_TEST_TOTP_SECRET", ""),
            "save_to_vault": True,
        }
        envelope = encrypt_for_broker(
            keypair.public_key_b64,
            payload,
            request_id=request.request_id,
            origin=request.origin,
            request_type=request.request_type,
        )
        RequestStore().submit_ciphertext(request.request_id, envelope)

    payload = _wait_for_request_payload(request.request_id)
    secret = CredentialSecret(
        username=str(payload["username"]),
        password=str(payload["password"]),
        totp_seed=payload.get("totp_seed") or None,
    )
    if should_save_to_vault(request, payload):
        credential_id = vault.add_credential(
            username=secret.username,
            password=secret.password,
            totp_seed=secret.totp_seed,
            allowed_origins=[origin],
        )
        AuditLog().append("credential_saved", origin=origin, credential_id=credential_id, request_id=request.request_id)
        return credential_id, vault.decrypt_credential(credential_id)
    credential_id = f"one_time:{request.request_id}"
    AuditLog().append("credential_ready_for_one_time_use", origin=origin, request_id=request.request_id, status="ok")
    return credential_id, secret


def _login(args, client: DemoHttpClient) -> str:
    origin = args.demo_origin.rstrip("/")
    credential_id, secret = _credential_from_control_or_vault(args, origin)
    client.get("/login")
    client.post("/login", {"email": secret.username, "password": secret.password})
    request = request_user_interaction(
        origin=origin,
        top_level_url=f"{origin}/totp",
        challenge_type="totp",
        reason="Demo TOTP verification",
        fields=["otp"],
        risk_level="low",
    )
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") == "1":
        complete_challenge(request.request_id)
        code = os.environ.get("OMNIDOER_TEST_SMS_CODE", "123456")
    else:
        code = _challenge_code_from_payload(_wait_for_challenge_payload(request.request_id))
    client.post("/totp", {"otp": code})
    AuditLog().append("login_completed", origin=origin, credential_id=credential_id, status="ok")
    return credential_id


def _invoice_task(args) -> int:
    client = DemoHttpClient(args.demo_origin)
    _login(args, client)
    output = Path(".omnidoer/downloads/omnidoer-demo-invoice.txt")
    client.download("/invoice/download", output)
    AuditLog().append("invoice_downloaded", origin=args.demo_origin, status="ok", path=str(output))
    print(f"invoice downloaded: {output}")
    return 0


def _captcha_task(args) -> int:
    client = DemoHttpClient(args.demo_origin)
    client.get("/captcha")
    request = request_user_interaction(
        origin=args.demo_origin,
        top_level_url=f"{args.demo_origin}/captcha",
        challenge_type="captcha",
        reason="Demo CAPTCHA requires user completion",
        fields=["ack"],
        risk_level="medium",
    )
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") == "1":
        complete_challenge(request.request_id)
        ack = os.environ.get("OMNIDOER_TEST_CAPTCHA_ACK", "user-completed")
        client.post("/captcha", {"ack": ack})
    print("challenge completed by user; bypassed=false")
    return 0


def _takeover_task(args) -> int:
    origin = args.demo_origin.rstrip("/")
    request = request_user_control(
        origin=origin,
        top_level_url=f"{origin}/antibot",
        reason="Demo high-intensity anti-bot requires user takeover",
        browser_context_id="demo-antibot",
    )
    if os.environ.get("OMNIDOER_TAKEOVER_TEST_MODE") == "1":
        with BrowserContextWorker(f"{origin}/antibot") as browser:
            with registered_browser_context("demo-antibot", browser):
                start_stream(request.request_id, browser_controller=browser)
                browser.click("#takeover")
                release_seen = False
                for event in parse_actions(os.environ.get("OMNIDOER_TEST_TAKEOVER_ACTIONS", "type:user-completed;release")):
                    if event.event_type == "release":
                        release_seen = True
                        break
                    if event.event_type == "type":
                        browser.click("#takeover")
                    apply_input_event(request.request_id, event, browser_controller=browser)
                browser.press_key("Enter")
                release_control(request.request_id)
    else:
        start_stream(request.request_id)
    print("human takeover completed by user; agent resumed")
    return 0


def _registration_task(args) -> int:
    origin = args.demo_origin.rstrip("/")
    request = request_registration_handoff(
        origin=origin,
        top_level_url=f"{origin}/register",
        reason="Demo site requires user account registration",
        browser_context_id="demo-registration",
        risk_level="medium",
    )
    if os.environ.get("OMNIDOER_TAKEOVER_TEST_MODE") == "1":
        with BrowserContextWorker(f"{origin}/register") as browser:
            with registered_browser_context("demo-registration", browser):
                start_stream(request.request_id, browser_controller=browser)
                interactions = [
                    ("#reg_email", os.environ.get("OMNIDOER_TEST_USERNAME", "new-demo@example.test")),
                    ("#reg_password", os.environ.get("OMNIDOER_TEST_PASSWORD", "demo-password-change-me")),
                    ("#reg_code", os.environ.get("OMNIDOER_TEST_EMAIL_CODE", "654321")),
                ]
                for selector, value in interactions:
                    browser.click(selector)
                    apply_input_event(request.request_id, InputEvent("type", text=value), browser_controller=browser)
                browser.click("#reg_terms")
                browser.click("#register-submit")
                if "/dashboard" not in browser.current_url():
                    raise RuntimeError("registration handoff did not reach dashboard")
                release_control(request.request_id)
    else:
        start_stream(request.request_id)
    AuditLog().append("registration_handoff_completed", origin=origin, request_id=request.request_id, status="ok")
    print("registration completed by user handoff; agent resumed")
    return 0


def _guarded_browser_task(args) -> int:
    origin = args.demo_origin.rstrip("/")
    credential_id, secret = _credential_from_control_or_vault(args, origin)
    browser_context_id = "demo-guarded-browser"
    with BrowserContextWorker(f"{origin}/login") as browser:
        with registered_browser_context(browser_context_id, browser):
            browser.fill_field("#email", secret.username, secret=True)
            browser.fill_field("#password", secret.password, secret=True)
            browser.click("button[type='submit']")
            browser.wait_for_load_state()
            first = resolve_current_browser_challenge(
                origin=origin,
                browser=browser,
                browser_context_id=browser_context_id,
                reason="Demo login requires user 2FA completion",
            )
            browser.wait_for_load_state()
            if "/dashboard" not in browser.current_url():
                raise RuntimeError("guarded browser login did not reach dashboard")

            browser.open(f"{origin}/antibot")
            second = resolve_current_browser_challenge(
                origin=origin,
                browser=browser,
                browser_context_id=browser_context_id,
                reason="Demo anti-bot requires user takeover",
            )
            browser.wait_for_load_state()
    AuditLog().append(
        "guarded_browser_task_completed",
        origin=origin,
        credential_id=credential_id,
        first_mode=first.mode,
        first_challenge_type=first.challenge_type,
        second_mode=second.mode,
        second_challenge_type=second.challenge_type,
        status="ok",
    )
    print("guarded browser task completed; 2FA and takeover handled; agent resumed")
    return 0


def _checkout_task(args) -> int:
    client = DemoHttpClient(args.demo_origin)
    _login(args, client)
    client.get("/checkout")
    request = request_approval(
        origin=args.demo_origin,
        top_level_url=f"{args.demo_origin}/checkout",
        action_summary="Submit local mock payment",
        risk_level="medium",
        structured_details={
            "merchant": "OmniDoer Local Demo Store",
            "amount": "12.34",
            "currency": "USD",
            "origin": args.demo_origin,
            "recipient": "OmniDoer Local Demo Store",
            "shipping_address": "No shipping required",
            "billing_method_summary": "Mock local payment method only",
            "subscription": "No subscription or auto-renewal",
            "refund_terms": "Demo payment has no real charge",
            "final_button": "Pay 12.34 USD",
            "after_approval": "Submit local mock payment and then request mock 3DS confirmation if shown",
        },
    )
    decision = decide(request.request_id)
    if decision != "approved":
        AuditLog().append("payment_denied", origin=args.demo_origin, request_id=request.request_id, status="denied")
        print("payment denied; not submitted")
        return 0
    RequestStore().consume_approval(request.request_id)

    challenge = request_user_interaction(
        origin=args.demo_origin,
        top_level_url=f"{args.demo_origin}/checkout/3ds",
        challenge_type="3ds",
        reason="Mock 3DS confirmation",
        fields=["code"],
        risk_level="medium",
    )
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") == "1":
        complete_challenge(challenge.request_id)
        code = os.environ.get("OMNIDOER_TEST_SMS_CODE", "123456")
    else:
        code = _challenge_code_from_payload(_wait_for_challenge_payload(challenge.request_id))
    client.post("/checkout/3ds", {"code": code})
    client.post(
        "/checkout/submit",
        {
            "merchant": "OmniDoer Local Demo Store",
            "amount": "12.34",
            "currency": "USD",
            "approval_status": "approved",
        },
    )
    AuditLog().append("mock_payment_submitted", origin=args.demo_origin, request_id=request.request_id, status="ok")
    print("mock payment submitted after approval")
    return 0


def run_task(args) -> int:
    task = args.task
    lowered = task.lower()
    if "guarded" in lowered or "2fa" in lowered or "二次验证" in task or "智能切换" in task:
        return _guarded_browser_task(args)
    if "下载" in task or "invoice" in task or "发票" in task:
        return _invoice_task(args)
    if "人机验证" in task or "captcha" in lowered:
        return _captcha_task(args)
    if "反机器人" in task or "anti" in lowered:
        return _takeover_task(args)
    if "注册" in task or "register" in lowered or "signup" in lowered:
        return _registration_task(args)
    if "checkout" in lowered or "支付" in task or "付款" in task:
        return _checkout_task(args)
    print("unsupported demo task")
    return 2

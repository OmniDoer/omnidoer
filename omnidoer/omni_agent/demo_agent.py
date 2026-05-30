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
from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_challenge.relay import complete_in_test_mode as complete_challenge
from omnidoer.omni_challenge.relay import request_user_interaction
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import decrypt_at_broker, encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_takeover.relay import complete_in_test_mode as complete_takeover
from omnidoer.omni_takeover.relay import request_user_control, start_stream
from omnidoer.omni_vault.models import CredentialSecret
from omnidoer.omni_vault.vault import Vault, _passphrase_from_env


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
    return Vault.load(args.vault, _passphrase_from_env(args.passphrase_env))


def _wait_for_request_payload(request_id: str, timeout_seconds: int = 300) -> dict:
    store = RequestStore()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        request = store.get(request_id)
        if request.response_ciphertext:
            keypair = load_or_create_keypair()
            return decrypt_at_broker(
                keypair.private_key_b64,
                request.response_ciphertext,
                request_id=request.request_id,
                origin=request.origin,
                request_type=request.request_type,
            )
        time.sleep(0.5)
    raise TimeoutError("timed out waiting for Control Client request")


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
    credential_id = vault.add_credential(
        username=payload["username"],
        password=payload["password"],
        totp_seed=payload.get("totp_seed") or None,
        allowed_origins=[origin],
    )
    AuditLog().append("credential_saved", origin=origin, credential_id=credential_id, request_id=request.request_id)
    return credential_id, vault.decrypt_credential(credential_id)


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
    client = DemoHttpClient(args.demo_origin)
    client.get("/antibot")
    request = request_user_control(
        origin=args.demo_origin,
        top_level_url=f"{args.demo_origin}/antibot",
        reason="Demo high-intensity anti-bot requires user takeover",
    )
    start_stream(request.request_id)
    if os.environ.get("OMNIDOER_TAKEOVER_TEST_MODE") == "1":
        complete_takeover(request.request_id)
        client.post("/antibot", {"takeover": "user-completed"})
    print("human takeover completed by user; agent resumed")
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
            "final_button": "Pay 12.34 USD",
        },
    )
    decision = decide(request.request_id)
    if decision != "approved":
        AuditLog().append("payment_denied", origin=args.demo_origin, request_id=request.request_id, status="denied")
        print("payment denied; not submitted")
        return 0

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
    client.post("/checkout/3ds", {"code": os.environ.get("OMNIDOER_TEST_SMS_CODE", "123456")})
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
    if "下载" in task or "invoice" in task or "发票" in task:
        return _invoice_task(args)
    if "人机验证" in task or "captcha" in task.lower():
        return _captcha_task(args)
    if "反机器人" in task or "anti" in task.lower():
        return _takeover_task(args)
    if "checkout" in task.lower() or "支付" in task or "付款" in task:
        return _checkout_task(args)
    print("unsupported demo task")
    return 2

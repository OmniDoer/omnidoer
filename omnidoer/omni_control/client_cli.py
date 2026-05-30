"""Linux CLI/TUI control client commands."""

from __future__ import annotations

import getpass
import json
import os

from omnidoer.omni_control.cloud import build_config, security_status
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.pairing import PairingStore, parse_duration_seconds, pairing_url, qr_text
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_control.server import serve
from omnidoer.omni_control.sessions import SessionStore
from omnidoer.omni_control.tasks import TaskStore


def _secret_payload(request) -> dict[str, str | bool]:
    if os.environ.get("OMNIDOER_CONTROL_TEST_MODE") == "1":
        return {
            "username": os.environ.get("OMNIDOER_TEST_USERNAME", "demo"),
            "password": os.environ.get("OMNIDOER_TEST_PASSWORD", ""),
            "totp_seed": os.environ.get("OMNIDOER_TEST_TOTP_SECRET", ""),
            "save_to_vault": True,
        }
    print("Secret will be encrypted to Secret Broker.")
    print("Secret will not be sent to LLM, MCP result, logs, or DOM observation.")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    totp_seed = getpass.getpass("TOTP seed (optional): ")
    save = input("Save encrypted in Vault? [y/N]: ").strip().lower() == "y"
    return {"username": username, "password": password, "totp_seed": totp_seed, "save_to_vault": save}


def _challenge_payload(request) -> dict[str, str]:
    env_map = {
        "sms_code": "OMNIDOER_TEST_SMS_CODE",
        "email_code": "OMNIDOER_TEST_EMAIL_CODE",
        "one_time_code": "OMNIDOER_TEST_ONE_TIME_CODE",
        "totp": "OMNIDOER_TEST_SMS_CODE",
        "payment_3ds": "OMNIDOER_TEST_SMS_CODE",
    }
    if os.environ.get("OMNIDOER_CHALLENGE_TEST_MODE") == "1":
        if request.request_type == "captcha":
            return {"ack": os.environ.get("OMNIDOER_TEST_CAPTCHA_ACK", "user-completed")}
        return {"code": os.environ.get(env_map.get(request.request_type, "OMNIDOER_TEST_ONE_TIME_CODE"), "")}
    print("Challenge will be completed by you, not by the Agent.")
    print("OmniDoer will not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS.")
    if request.request_type == "captcha":
        input("Complete the CAPTCHA in the Control Client, then press Enter: ")
        return {"ack": "user-completed"}
    return {"code": getpass.getpass("Challenge code: ")}


def _submit_encrypted(request_id: str, payload: dict) -> None:
    store = RequestStore()
    request = store.get(request_id)
    keypair = load_or_create_keypair()
    envelope = encrypt_for_broker(
        keypair.public_key_b64,
        payload,
        request_id=request.request_id,
        origin=request.origin,
        request_type=request.request_type,
    )
    store.submit_ciphertext(request.request_id, envelope)


def handle_control_command(args) -> int:
    command = args.control_command
    if command == "serve":
        serve(
            args.host,
            args.port,
            public_url=args.public_url,
            cloud_direct=args.cloud_direct,
            tls_cert=args.tls_cert,
            tls_key=args.tls_key,
            tls_self_signed_dev=args.tls_self_signed_dev,
            behind_reverse_proxy=args.behind_reverse_proxy,
            insecure_dev_public=args.insecure_dev_public,
        )
        return 0
    if command == "pair":
        public_url = args.public_url or os.environ.get("OMNIDOER_CONTROL_PUBLIC_URL") or "http://127.0.0.1:8787"
        pairing = PairingStore().create(public_url=public_url, ttl_seconds=parse_duration_seconds(args.expires))
        print(f"pairing_url={pairing_url(pairing)}")
        print(f"expires_at={pairing.expires_at}")
        print(f"broker_fingerprint={pairing.broker_fingerprint}")
        print("warning=Only pair devices you control.")
        if args.print_qr:
            print(qr_text(pairing))
        return 0
    if command == "status":
        pending = len(RequestStore().list())
        print(f"OmniDoer Control Client: local trusted mode, pending_requests={pending}")
        return 0
    if command == "devices":
        print(json.dumps([device.to_public_dict() for device in DeviceStore().list()], indent=2, sort_keys=True))
        return 0
    if command == "revoke-device":
        DeviceStore().revoke(args.device_id)
        print(f"revoked device {args.device_id}")
        return 0
    if command == "sessions":
        print(json.dumps([session.to_public_dict() for session in SessionStore().list()], indent=2, sort_keys=True))
        return 0
    if command == "revoke-session":
        SessionStore().revoke(args.session_id)
        print(f"revoked session {args.session_id}")
        return 0
    if command == "tunnel-info":
        print("Cloud Direct uses direct HTTPS/WSS to your own server. No third-party relay is configured.")
        return 0
    if command == "security-status":
        config = build_config(
            host=os.environ.get("OMNIDOER_CONTROL_HOST", "127.0.0.1"),
            port=int(os.environ.get("OMNIDOER_CONTROL_PORT", "8787")),
            public_url=os.environ.get("OMNIDOER_CONTROL_PUBLIC_URL"),
            cloud_direct=os.environ.get("OMNIDOER_CONTROL_CLOUD_DIRECT") == "1",
            behind_reverse_proxy=os.environ.get("OMNIDOER_CONTROL_BEHIND_PROXY") == "1",
            tls_self_signed_dev=os.environ.get("OMNIDOER_CONTROL_TLS_SELF_SIGNED_DEV") == "1",
            insecure_dev_public=os.environ.get("OMNIDOER_CONTROL_INSECURE_DEV_PUBLIC") == "1",
        )
        print(json.dumps(security_status(config), indent=2, sort_keys=True))
        return 0
    if command == "tui":
        print("OmniDoer Control TUI")
        print("Secret destination: Secret Broker. Not sent to Agent/LLM context.")
        print("Challenge destination: Challenge Relay / target website. OmniDoer does not bypass challenges.")
        print("Takeover destination: controlled browser. Agent paused while user is in control.")
        return 0
    if command == "requests":
        print(json.dumps([request.to_public_dict() for request in RequestStore().list()], indent=2, sort_keys=True))
        return 0
    if command == "submit-task":
        task = TaskStore().create(args.task, source="control_cli")
        print(f"queued task {task.task_id}; Codex can read it with control.next_user_task")
        return 0
    if command == "tasks":
        print(json.dumps([task.to_public_dict() for task in TaskStore().list(include_completed=True)], indent=2, sort_keys=True))
        return 0
    if command == "complete-task":
        TaskStore().complete(args.task_id)
        print(f"completed {args.task_id}")
        return 0
    if command == "cancel-task":
        TaskStore().cancel(args.task_id)
        print(f"cancelled {args.task_id}")
        return 0
    if command == "approve":
        RequestStore().approve(args.request_id)
        print(f"approved {args.request_id}")
        return 0
    if command == "deny":
        RequestStore().deny(args.request_id)
        print(f"denied {args.request_id}")
        return 0
    if command == "input-secret":
        request = RequestStore().get(args.request_id)
        _submit_encrypted(args.request_id, _secret_payload(request))
        print(f"secret submitted to Secret Broker for {args.request_id}; secret_exposed_to_model=false")
        return 0
    if command == "challenge":
        request = RequestStore().get(args.request_id)
        payload = _challenge_payload(request)
        _submit_encrypted(args.request_id, payload)
        RequestStore().mark_challenge_completed(args.request_id)
        print(f"challenge completed by user for {args.request_id}; bypassed=false")
        return 0
    if command == "takeover":
        request = RequestStore().get(args.request_id)
        print(f"Agent paused. User in control for {request.origin}. Release when finished.")
        return 0
    if command == "release":
        RequestStore().release_takeover(args.request_id)
        print(f"released {args.request_id}; agent resumed")
        return 0
    return 0

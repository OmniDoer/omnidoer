"""Linux CLI/TUI control client commands."""

from __future__ import annotations

import getpass
import json
import os
import shlex
import sys
import time

from omnidoer.omni_control.cloud import build_config, security_status
from omnidoer.omni_control.chat import ChatStore
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.pairing import PairingStore, parse_duration_seconds, pairing_url, qr_text
from omnidoer.omni_control.requests import RequestStore, wait_for_request_completion
from omnidoer.omni_control.runtime import resolve_pairing_public_url
from omnidoer.omni_control.secure_channel import encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_control.server import serve
from omnidoer.omni_control.sessions import SessionStore
from omnidoer.omni_control.tasks import TaskStore


def print_pairing_invite(*, public_url: str | None = None, expires: str = "24h", print_qr: bool = True) -> None:
    public_url = resolve_pairing_public_url(public_url)
    pairing = PairingStore().create(public_url=public_url, ttl_seconds=parse_duration_seconds(expires))
    print("OmniDoer Control Client pairing")
    if print_qr:
        print("qr_ascii_begin")
        print(qr_text(pairing, ansi=sys.stdout.isatty()))
        print("qr_ascii_end")
    print(f"pairing_url={pairing_url(pairing)}")
    print(f"expires_at={pairing.expires_at}")
    print(f"max_uses={pairing.max_uses}")
    print(f"broker_fingerprint={pairing.broker_fingerprint}")
    print("warning=Only pair devices you control. Pairing URLs are reusable up to 10 times within 24 hours by default.")


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
        device_id=request.allowed_device_id,
        expires_at=request.expires_at,
    )
    store.submit_ciphertext(request.request_id, envelope)


def _collect_sync_status(thread_id: str | None = None, codex_bin: str | None = None) -> dict:
    from omnidoer.omni_control.chat_runner import (
        active_tui_process_bridge_status,
        control_chat_sync_diagnostics,
        live_tui_bridge_active,
        live_tui_session_active,
        native_console_bridge_install_status,
        tui_bridge_heartbeat_status,
        tui_restart_command,
    )
    from omnidoer.omni_control.tui_legacy_relay import legacy_tui_relay_status

    resolved_thread_id = thread_id or os.environ.get("OMNIDOER_CHAT_THREAD_ID")
    bridge_heartbeat = tui_bridge_heartbeat_status(resolved_thread_id)
    tui_bridge_active = live_tui_bridge_active(resolved_thread_id)
    tui_session_active = live_tui_session_active(resolved_thread_id)
    legacy_relay = legacy_tui_relay_status(resolved_thread_id) if resolved_thread_id and not tui_bridge_active else {"active": False}
    install_status = native_console_bridge_install_status(codex_bin)
    active_process_bridge = active_tui_process_bridge_status(resolved_thread_id, codex_bin=codex_bin)
    diagnostics = control_chat_sync_diagnostics(
        thread_id=resolved_thread_id,
        tui_bridge_active=tui_bridge_active,
        tui_session_active=tui_session_active,
        install_status=install_status,
        legacy_relay=legacy_relay,
        active_process_bridge=active_process_bridge,
        bridge_heartbeat_age_seconds=bridge_heartbeat.get("age_seconds"),
        bridge_heartbeat=bridge_heartbeat,
    )
    return {
        "thread_id": resolved_thread_id,
        "tui_bridge_active": tui_bridge_active,
        "tui_session_active": tui_session_active,
        "restart_command": tui_restart_command(resolved_thread_id) if diagnostics["requires_restart_for_native_sync"] else None,
        "native_console_bridge": install_status,
        "active_tui_process_bridge": active_process_bridge,
        "bridge_heartbeat": bridge_heartbeat,
        "legacy_tui_relay": legacy_relay,
        "sync_diagnostics": diagnostics,
    }


def _wait_for_native_sync_status(
    *,
    thread_id: str | None = None,
    codex_bin: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict:
    deadline = time.time() + max(0.0, timeout_seconds)
    last_status = _collect_sync_status(thread_id, codex_bin)
    while time.time() <= deadline:
        if last_status["sync_diagnostics"]["native_sync_active"]:
            return {"verified": True, "sync_status": last_status}
        time.sleep(0.5)
        last_status = _collect_sync_status(thread_id, codex_bin)
    return {"verified": False, "sync_status": last_status}


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
            chat_runner=args.chat_runner,
            chat_runner_interval=args.chat_runner_interval,
            chat_runner_cwd=args.chat_runner_cwd,
            chat_codex_bin=args.chat_codex_bin,
            chat_thread_id=args.chat_thread_id,
            chat_codex_args=args.chat_codex_arg,
            chat_upload_ttl=args.chat_upload_ttl,
            chat_allow_detached_thread_resume=args.chat_allow_detached_thread_resume,
        )
        return 0
    if command == "pair":
        print_pairing_invite(public_url=args.public_url, expires=args.expires, print_qr=args.print_qr)
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
        revoked_sessions = SessionStore().revoke_for_device(args.device_id)
        print(f"revoked device {args.device_id}; revoked_sessions={len(revoked_sessions)}")
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
    if command == "sync-status":
        print(json.dumps(_collect_sync_status(args.thread_id, args.codex_bin), indent=2, sort_keys=True))
        return 0
    if command == "enable-sync":
        status = _collect_sync_status(args.thread_id, args.codex_bin)
        diagnostics = status["sync_diagnostics"]
        if not args.yes:
            rerun = ["omnidoer", "control", "enable-sync", "--yes"]
            if status["thread_id"]:
                rerun.extend(["--thread-id", status["thread_id"]])
            if args.codex_bin:
                rerun.extend(["--codex-bin", args.codex_bin])
            if args.wait:
                rerun.append("--wait")
                rerun.extend(["--timeout", args.timeout])
            print(
                json.dumps(
                    {
                        "status": "dry_run",
                        "confirmation_required": True,
                        "rerun_with": " ".join(shlex.quote(part) for part in rerun),
                        "would_restart_current_console": bool(diagnostics["restart_current_console_available"]),
                        "sync_status": status,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        timeout_seconds = parse_duration_seconds(args.timeout)
        if not diagnostics["restart_current_console_available"]:
            print(
                json.dumps(
                    {
                        "status": "not_ready",
                        "error": "restart_current_console_unavailable",
                        "sync_status": status,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 2
        from omnidoer.omni_control.tui_legacy_relay import restart_tmux_pane_for_bridge

        result = restart_tmux_pane_for_bridge(
            status["thread_id"],
            restart_command=status["restart_command"],
        )
        verification = None
        if args.wait:
            verification = _wait_for_native_sync_status(
                thread_id=status["thread_id"],
                codex_bin=args.codex_bin,
                timeout_seconds=timeout_seconds,
            )
        response = {
            "status": "restart_started",
            "result": result,
            "sync_status_before_restart": status,
        }
        if verification is not None:
            response["verified"] = verification["verified"]
            response["sync_status_after_restart"] = verification["sync_status"]
            response["status"] = "native_sync_active" if verification["verified"] else "restart_started_wait_timeout"
        print(
            json.dumps(
                response,
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if verification is None or verification["verified"] else 1
    if command == "wait-request":
        print("waiting_for_control_client=true", flush=True)
        request = wait_for_request_completion(
            args.request_id,
            timeout_seconds=parse_duration_seconds(args.timeout),
        )
        print(f"request_id={request.request_id}")
        print("request_completed=true")
        print(f"status={request.status}")
        print(f"completed_by_user={str(request.completed_by_user).lower()}")
        print(f"has_ciphertext={str(request.response_ciphertext is not None).lower()}")
        print("secret_exposed_to_model=false")
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
    if command == "chat-send":
        message = ChatStore().append(role="user", text=args.message, source="control_cli")
        print(f"queued chat message {message.message_id}; Agent can read it with control.next_user_message")
        return 0
    if command == "chat-log-user":
        message = ChatStore().append(
            role="user",
            text=args.message,
            status="completed",
            source=args.source,
        )
        print(f"published user chat message {message.message_id}")
        return 0
    if command == "chat-messages":
        print(json.dumps([message.to_public_dict() for message in ChatStore().list()], indent=2, sort_keys=True))
        return 0
    if command == "chat-next":
        message = ChatStore().next_user_message(claim=not args.no_claim)
        if message is None:
            print(json.dumps({"status": "empty", "secret_fields_allowed": False}, indent=2, sort_keys=True))
        else:
            print(json.dumps({"status": "ok", "message": message.to_public_dict()}, indent=2, sort_keys=True))
        return 0
    if command == "chat-reply":
        message = ChatStore().append(
            role="assistant",
            text=args.message,
            source="control_cli",
            reply_to_message_id=args.reply_to,
        )
        print(f"published chat message {message.message_id}")
        return 0
    if command == "chat-record":
        record = ChatStore().append_record(
            record_type=args.record_type,
            text=args.text,
            role=args.role,
            message_id=args.message_id,
            source="control_cli",
        )
        print(f"published chat record {record.record_id}")
        return 0
    if command == "chat-start":
        message = ChatStore().append(
            role="assistant",
            text="",
            status="streaming",
            source=args.source,
            reply_to_message_id=args.reply_to,
        )
        print(message.message_id)
        return 0
    if command == "chat-delta":
        message = ChatStore().append_delta(args.message_id, args.delta)
        print(f"updated chat message {message.message_id}")
        return 0
    if command == "chat-complete":
        message = ChatStore().complete(args.message_id, text=args.text)
        print(f"completed chat message {message.message_id}")
        return 0
    if command == "chat-run-next":
        from omnidoer.omni_control.chat_runner import ChatRunner

        message = ChatRunner(
            codex_bin=args.codex_bin,
            cwd=args.cwd,
            thread_id=args.thread_id,
            extra_args=args.codex_arg,
            allow_detached_thread_resume=args.allow_detached_thread_resume,
        ).run_once()
        if message is None:
            print("no queued chat messages")
            return 0
        print(f"processed chat message {message.message_id}")
        return 0
    if command == "chat-runner":
        from omnidoer.omni_control.chat_runner import ChatRunner

        print("chat_runner_started=true", flush=True)
        ChatRunner(
            codex_bin=args.codex_bin,
            cwd=args.cwd,
            thread_id=args.thread_id,
            extra_args=args.codex_arg,
            poll_interval=args.interval,
            allow_detached_thread_resume=args.allow_detached_thread_resume,
        ).run_forever()
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
        if request.request_type not in {"captcha", "passkey", "webauthn", "device_confirmation"}:
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

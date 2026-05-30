"""MCP tool registry and status-only dispatch."""

from __future__ import annotations

import os

ALLOWED_TOOLS = [
    "browser.open",
    "browser.observe",
    "browser.observe_accessibility",
    "browser.click",
    "browser.type_text",
    "browser.select",
    "browser.upload_file",
    "browser.download_current_file",
    "browser.current_origin",
    "browser.detect_challenge",
    "browser.detect_antibot",
    "credential.list_for_current_origin",
    "credential.create_interactive",
    "credential.request_from_user",
    "credential.fill_current_origin_login",
    "credential.fill_current_origin_totp",
    "challenge.request_user_interaction",
    "challenge.status",
    "registration.request_user_handoff",
    "takeover.request_user_control",
    "takeover.status",
    "approval.request",
    "payment.prepare_review",
    "payment.request_user_approval",
    "audit.show_recent_events",
    "policy.explain_current_block",
    "control.list_requests",
    "control.request_status",
    "control.list_tasks",
    "control.next_user_task",
]


def forbidden_tool_names() -> set[str]:
    return {
        "credential." + "get_" + "password",
        "credential." + "decrypt",
        "credential." + "get_" + "totp",
        "credential." + "get_" + "cookie",
        "vault." + "export",
        "browser." + "dump_" + "cookies",
        "browser." + "dump_local_" + "storage",
        "browser." + "dump_" + "password_values",
        "secret." + "read",
        "secret." + "print",
        "secret." + "copy_to_clipboard",
        "captcha." + "solve",
        "captcha." + "bypass",
        "mfa." + "bypass",
        "antibot." + "bypass",
        "webauthn." + "export_" + "private_key",
        "passkey." + "export_" + "private_key",
        "challenge." + "get_answer",
        "takeover." + "get_user_input",
    }


def tool_descriptors() -> list[dict]:
    return [
        {
            "name": name,
            "description": f"OmniDoer safe action tool {name}",
            "inputSchema": {"type": "object", "additionalProperties": True},
        }
        for name in ALLOWED_TOOLS
    ]


def _error(status: str, message: str) -> dict:
    return {"status": status, "error": message, "secret_exposed_to_model": False}


def _origin_and_url(arguments: dict) -> tuple[str | None, str | None]:
    origin = arguments.get("origin")
    top_level_url = arguments.get("top_level_url") or arguments.get("url")
    if top_level_url and not origin:
        from omnidoer.omni_policy.policy import origin_from_url

        origin = origin_from_url(str(top_level_url))
    if origin and top_level_url:
        return str(origin), str(top_level_url)
    try:
        from omnidoer.omni_mcp.runtime import get_browser

        browser = get_browser()
        return str(origin or browser.current_origin() or ""), str(top_level_url or browser.current_url())
    except Exception:
        return (str(origin) if origin else None), (str(top_level_url) if top_level_url else None)


def _fields(arguments: dict) -> list[str]:
    value = arguments.get("fields") or arguments.get("requested_fields") or []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _vault_path(arguments: dict) -> str:
    return str(arguments.get("vault_path") or arguments.get("vault") or ".omnidoer/vault.json")


def _vault_passphrase(arguments: dict) -> str | None:
    env_name = arguments.get("passphrase_env") or os.environ.get("OMNIDOER_VAULT_PASSPHRASE_ENV")
    if env_name:
        return os.environ.get(str(env_name))
    return None


def _create_credential_request(arguments: dict) -> dict:
    from omnidoer.omni_control.requests import RequestStore
    from omnidoer.omni_control.secure_channel import load_or_create_keypair

    origin, top_level_url = _origin_and_url(arguments)
    if not origin or not top_level_url:
        return _error("error", "origin or active browser required")
    request = RequestStore().create(
        "credential",
        origin=origin,
        top_level_url=top_level_url,
        action_summary=str(arguments.get("reason") or arguments.get("action_summary") or "credential requested"),
        risk_level=str(arguments.get("risk_level") or "medium"),
        broker_public_key_fingerprint=load_or_create_keypair().fingerprint,
        requested_fields=_fields(arguments) or ["username", "password"],
        save_to_vault=bool(arguments.get("save_to_vault", True)),
    )
    return {"status": "credential_request_created", "request": request.to_public_dict(), "secret_exposed_to_model": False}


def _file_upload_allowed(arguments: dict, *, origin: str | None, top_level_url: str, file_path: str, selector: str) -> dict | None:
    if not arguments.get("sensitive"):
        return None

    from pathlib import Path

    from omnidoer.omni_control.requests import RequestStore

    store = RequestStore()
    request_id = arguments.get("approval_request_id") or arguments.get("request_id")
    if request_id:
        try:
            request = store.get(str(request_id))
        except KeyError:
            return _error("not_found", "file upload approval request not found")
        if request.request_type != "file_upload":
            return _error("rejected", "approval request is not for file upload")
        if request.status != "approved":
            return {
                "status": "approval_required",
                "request": request.to_public_dict(),
                "secret_exposed_to_model": False,
            }
        if origin and request.origin != origin:
            return _error("rejected", "file upload approval origin mismatch")
        return None

    request = store.create(
        "file_upload",
        origin=origin or "",
        top_level_url=top_level_url,
        action_summary=str(arguments.get("action_summary") or "sensitive file upload approval required"),
        risk_level=str(arguments.get("risk_level") or "high"),
        structured_details={
            "filename": Path(file_path).name,
            "selector": selector,
            "sensitive": True,
            "after_approval": "Upload the selected local file to the current browser file input",
        },
    )
    return {
        "status": "approval_required",
        "request": request.to_public_dict(),
        "secret_exposed_to_model": False,
    }


def _totp_code(seed: str) -> str:
    import base64
    import hashlib
    import hmac
    import struct
    import time

    normalized = seed.replace(" ", "").upper()
    padded = normalized + ("=" * ((8 - len(normalized) % 8) % 8))
    key = base64.b32decode(padded)
    counter = int(time.time() // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def call_tool(name: str, arguments: dict | None = None) -> dict:
    if name not in ALLOWED_TOOLS:
        raise KeyError(name)
    arguments = arguments or {}
    if name.startswith("browser."):
        try:
            from omnidoer.omni_mcp.runtime import get_browser

            browser = get_browser()
            if name == "browser.open":
                url = arguments.get("url")
                if not url:
                    return _error("error", "url required")
                return browser.open(str(url))
            if name == "browser.observe":
                return {"status": "ok", "observation": browser.observe_dom(), "secret_exposed_to_model": False}
            if name == "browser.observe_accessibility":
                return {"status": "ok", "observation": browser.observe_accessibility(), "secret_exposed_to_model": False}
            if name == "browser.click":
                selector = arguments.get("selector") or arguments.get("selector_or_description")
                if not selector:
                    return _error("error", "selector required")
                return browser.click(str(selector))
            if name == "browser.type_text":
                if arguments.get("secret"):
                    return _error("rejected", "browser.type_text is for ordinary text; use credential tools for secrets")
                selector = arguments.get("selector") or arguments.get("selector_or_description")
                text = arguments.get("text")
                if not selector:
                    return _error("error", "selector required")
                if text is None:
                    return _error("error", "text required")
                return browser.type_text(str(selector), str(text))
            if name == "browser.select":
                selector = arguments.get("selector") or arguments.get("selector_or_description")
                value = arguments.get("value")
                if not selector:
                    return _error("error", "selector required")
                if value is None:
                    return _error("error", "value required")
                return browser.select(str(selector), str(value))
            if name == "browser.upload_file":
                selector = arguments.get("selector") or arguments.get("selector_or_description")
                file_path = arguments.get("path") or arguments.get("file_path")
                if not selector:
                    return _error("error", "selector required")
                if not file_path:
                    return _error("error", "path required")
                approval = _file_upload_allowed(
                    arguments,
                    origin=browser.current_origin(),
                    top_level_url=browser.current_url(),
                    file_path=str(file_path),
                    selector=str(selector),
                )
                if approval is not None:
                    return approval
                return browser.upload_file(str(selector), str(file_path))
            if name == "browser.download_current_file":
                selector = str(arguments.get("selector") or arguments.get("selector_or_description") or "a[download]")
                path = browser.download_current_file(selector=selector, output_dir=arguments.get("output_dir"))
                return {"status": "downloaded", "path": str(path), "secret_exposed_to_model": False}
            if name == "browser.current_origin":
                return {"status": "ok", "origin": browser.current_origin(), "url": browser.current_url(), "secret_exposed_to_model": False}
            if name == "browser.detect_challenge":
                challenge_type = browser.detect_challenge()
                return {
                    "status": "ok",
                    "challenge_type": challenge_type,
                    "requires_user_interaction": bool(challenge_type),
                    "secret_exposed_to_model": False,
                }
            if name == "browser.detect_antibot":
                detected = browser.detect_antibot()
                return {
                    "status": "ok",
                    "antibot_detected": detected,
                    "requires_human_takeover": detected,
                    "secret_exposed_to_model": False,
                }
        except Exception as exc:
            return _error("unavailable", type(exc).__name__)
    if name in {"credential.request_from_user", "credential.create_interactive"}:
        return _create_credential_request(arguments)
    if name == "credential.list_for_current_origin":
        from pathlib import Path

        from omnidoer.omni_vault.vault import Vault

        origin, _top_level_url = _origin_and_url(arguments)
        vault_path = Path(_vault_path(arguments))
        credentials = []
        if origin and vault_path.exists():
            vault = Vault.load(vault_path)
            credentials = [
                {
                    "credential_id": item.credential_id,
                    "username": item.username,
                    "allowed_origins": item.allowed_origins,
                    "metadata": item.metadata,
                }
                for item in vault.find_for_origin(origin)
            ]
        return {"status": "ok", "origin": origin, "credentials": credentials, "secret_exposed_to_model": False}
    if name in {"credential.fill_current_origin_login", "credential.fill_current_origin_totp"}:
        from omnidoer.omni_broker.broker import validate_fill
        from omnidoer.omni_mcp.runtime import get_browser
        from omnidoer.omni_vault.vault import Vault

        passphrase = _vault_passphrase(arguments)
        if passphrase is None:
            return _error("locked", "passphrase_env is required for vault-backed MCP fill")
        browser = get_browser()
        current_url = browser.current_url()
        current_origin = browser.current_origin()
        if not current_origin:
            return _error("error", "active browser origin required")
        vault = Vault.load(_vault_path(arguments), passphrase)
        credential_id = arguments.get("credential_id")
        metadata_items = vault.list_metadata()
        if credential_id is None:
            matches = [item for item in metadata_items if current_origin in item.allowed_origins]
            if not matches:
                return _error("not_found", "no credential for current origin")
            credential_id = matches[0].credential_id
        metadata = next((item for item in metadata_items if item.credential_id == credential_id), None)
        if metadata is None:
            return _error("not_found", "credential not found")
        try:
            validate_fill(current_url, metadata.allowed_origins, browser.inspect_form_action())
            secret = vault.decrypt_credential(str(credential_id))
        except PermissionError as exc:
            return {"status": "blocked", "reason": str(exc), "secret_exposed_to_model": False}
        except Exception as exc:
            return _error("unavailable", type(exc).__name__)
        if name == "credential.fill_current_origin_login":
            username_selector = str(
                arguments.get("username_selector")
                or "input[autocomplete='username'], input[name='email'], input[name='username'], #email, #username"
            )
            password_selector = str(arguments.get("password_selector") or "input[type='password']")
            browser.fill_field(username_selector, secret.username, secret=True)
            browser.fill_field(password_selector, secret.password, secret=True)
            return {
                "status": "credential_received_and_filled",
                "origin": current_origin,
                "fields": ["username", "password"],
                "credential_id": str(credential_id),
                "secret_exposed_to_model": False,
            }
        if not secret.totp_seed:
            return _error("not_found", "credential has no TOTP seed")
        totp_selector = str(arguments.get("totp_selector") or "input[autocomplete='one-time-code'], input[name='otp'], input[name='code'], #otp, #code")
        browser.fill_field(totp_selector, _totp_code(secret.totp_seed), secret=True)
        return {
            "status": "totp_filled",
            "origin": current_origin,
            "fields": ["totp"],
            "credential_id": str(credential_id),
            "secret_exposed_to_model": False,
        }
    if name == "challenge.request_user_interaction":
        from omnidoer.omni_challenge.relay import request_user_interaction

        origin, top_level_url = _origin_and_url(arguments)
        challenge_type = arguments.get("challenge_type")
        if not origin or not top_level_url:
            return _error("error", "origin or active browser required")
        if not challenge_type:
            return _error("error", "challenge_type required")
        request = request_user_interaction(
            origin=origin,
            top_level_url=top_level_url,
            challenge_type=str(challenge_type),
            reason=str(arguments.get("reason") or "user challenge interaction required"),
            fields=_fields(arguments),
            risk_level=str(arguments.get("risk_level") or "medium"),
        )
        return {"status": "challenge_request_created", "request": request.to_public_dict(), "secret_exposed_to_model": False}
    if name == "challenge.status":
        from omnidoer.omni_control.requests import RequestStore

        request_id = arguments.get("request_id")
        if not request_id:
            return _error("error", "request_id required")
        try:
            request = RequestStore().get(str(request_id))
        except KeyError:
            return {"status": "not_found", "secret_exposed_to_model": False}
        return {
            "status": request.status,
            "request": request.to_public_dict(),
            "completed_by_user": request.completed_by_user,
            "bypassed": request.bypassed,
            "secret_exposed_to_model": False,
        }
    if name == "registration.request_user_handoff":
        from omnidoer.omni_takeover.relay import request_registration_handoff

        origin, top_level_url = _origin_and_url(arguments)
        if not origin or not top_level_url:
            return _error("error", "origin or active browser required")
        request = request_registration_handoff(
            origin=origin,
            top_level_url=top_level_url,
            reason=str(arguments.get("reason") or "account registration must be completed by the user"),
            browser_context_id="mcp-browser",
            risk_level=str(arguments.get("risk_level") or "medium"),
            allowed_device_id=arguments.get("allowed_device_id"),
        )
        return {
            "status": "registration_handoff_created",
            "request": request.to_public_dict(),
            "agent_paused": True,
            "completed_by_user": False,
            "secret_exposed_to_model": False,
        }
    if name == "takeover.request_user_control":
        from omnidoer.omni_takeover.relay import request_user_control

        origin, top_level_url = _origin_and_url(arguments)
        if not origin or not top_level_url:
            return _error("error", "origin or active browser required")
        request = request_user_control(
            origin=origin,
            top_level_url=top_level_url,
            reason=str(arguments.get("reason") or "human takeover required"),
            browser_context_id="mcp-browser",
            risk_level=str(arguments.get("risk_level") or "high"),
        )
        return {"status": "takeover_request_created", "request": request.to_public_dict(), "secret_exposed_to_model": False}
    if name == "takeover.status":
        from omnidoer.omni_control.requests import RequestStore

        request_id = arguments.get("request_id")
        if not request_id:
            return _error("error", "request_id required")
        try:
            request = RequestStore().get(str(request_id))
        except KeyError:
            return {"status": "not_found", "secret_exposed_to_model": False}
        return {
            "status": request.status,
            "control_owner": request.control_owner,
            "completed_by_user": request.completed_by_user,
            "bypassed": request.bypassed,
            "secret_exposed_to_model": False,
        }
    if name == "approval.request":
        from omnidoer.omni_approval.approval import request_approval

        origin, top_level_url = _origin_and_url(arguments)
        if not origin or not top_level_url:
            return _error("error", "origin or active browser required")
        request = request_approval(
            origin=origin,
            top_level_url=top_level_url,
            action_summary=str(arguments.get("action_summary") or "approval required"),
            risk_level=str(arguments.get("risk_level") or "high"),
            structured_details=dict(arguments.get("structured_details") or {}),
        )
        return {"status": "approval_request_created", "request": request.to_public_dict(), "secret_exposed_to_model": False}
    if name == "payment.prepare_review":
        origin, top_level_url = _origin_and_url(arguments)
        return {
            "status": "payment_review_prepared",
            "origin": origin,
            "top_level_url": top_level_url,
            "requires_user_approval": True,
            "secret_exposed_to_model": False,
        }
    if name == "payment.request_user_approval":
        return call_tool("approval.request", {**arguments, "action_summary": arguments.get("action_summary") or "payment approval required"})
    if name == "control.list_requests":
        from omnidoer.omni_control.requests import RequestStore

        return {"status": "ok", "requests": [req.to_public_dict() for req in RequestStore().list()], "secret_exposed_to_model": False}
    if name == "control.request_status":
        from omnidoer.omni_control.requests import RequestStore

        request_id = (arguments or {}).get("request_id")
        if not request_id:
            return {"status": "error", "error": "request_id required", "secret_exposed_to_model": False}
        try:
            request = RequestStore().get(str(request_id))
        except KeyError:
            return {"status": "not_found", "secret_exposed_to_model": False}
        return {"status": "ok", "request": request.to_public_dict(), "secret_exposed_to_model": False}
    if name == "control.list_tasks":
        from omnidoer.omni_control.tasks import TaskStore

        return {
            "status": "ok",
            "tasks": [task.to_public_dict() for task in TaskStore().list(include_completed=True)],
            "secret_exposed_to_model": False,
            "submitted_to_openai_api_by_control_client": False,
        }
    if name == "control.next_user_task":
        from omnidoer.omni_control.tasks import TaskStore

        task = TaskStore().next_pending(claim=True)
        if task is None:
            return {
                "status": "empty",
                "secret_exposed_to_model": False,
                "submitted_to_openai_api_by_control_client": False,
            }
        return {
            "status": "ok",
            "task": task.to_public_dict(),
            "secret_exposed_to_model": False,
            "submitted_to_openai_api_by_control_client": False,
        }
    if name == "audit.show_recent_events":
        from omnidoer.omni_audit.audit import AuditLog

        return {"status": "ok", "events": AuditLog().tail(), "secret_exposed_to_model": False}
    if name == "policy.explain_current_block":
        from omnidoer.omni_policy.policy import evaluate_challenge, requires_approval

        action_type = str(arguments.get("action_type") or arguments.get("challenge_type") or "")
        if action_type:
            challenge_decision = evaluate_challenge(action_type)
            if challenge_decision.decision.value != "allow":
                return {
                    "status": "blocked",
                    "decision": challenge_decision.decision.value,
                    "reason": challenge_decision.reason,
                    "secret_exposed_to_model": False,
                }
            approval_decision = requires_approval(action_type)
            return {
                "status": "ok" if approval_decision.decision.value == "allow" else "blocked",
                "decision": approval_decision.decision.value,
                "reason": approval_decision.reason,
                "secret_exposed_to_model": False,
            }
        return {
            "status": "ok",
            "decision": "allow",
            "reason": "no current policy block",
            "secret_exposed_to_model": False,
        }
    return {"status": "ok", "tool": name, "secret_exposed_to_model": False}

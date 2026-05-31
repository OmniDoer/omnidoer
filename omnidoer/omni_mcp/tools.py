"""MCP tool registry and status-only dispatch."""

from __future__ import annotations

import os
from pathlib import Path

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
    "control.create_pairing",
    "control.list_requests",
    "control.request_status",
    "control.wait_request",
    "control.list_tasks",
    "control.next_user_task",
    "control.list_chat_messages",
    "control.list_chat_records",
    "control.next_user_message",
    "control.publish_chat_record",
    "control.publish_chat_message",
    "control.append_chat_message_delta",
    "control.complete_chat_message",
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


def _credential_structured_details(arguments: dict) -> dict:
    labels = dict(arguments.get("credential_labels") or arguments.get("field_labels") or {})
    for field, argument_name in (
        ("username", "username_label"),
        ("password", "password_label"),
        ("totp_seed", "totp_label"),
    ):
        if arguments.get(argument_name):
            labels[field] = str(arguments[argument_name])
    return {"credential_labels": labels} if labels else {}


def _vault_path(arguments: dict) -> str:
    return str(arguments.get("vault_path") or arguments.get("vault") or ".omnidoer/vault.json")


def _vault_passphrase(arguments: dict) -> str | None:
    env_name = arguments.get("passphrase_env") or os.environ.get("OMNIDOER_VAULT_PASSPHRASE_ENV")
    file_path = arguments.get("passphrase_file") or os.environ.get("OMNIDOER_VAULT_PASSPHRASE_FILE")
    if env_name and file_path:
        raise ValueError("use either passphrase_env or passphrase_file, not both")
    if file_path:
        return Path(str(file_path)).read_text().splitlines()[0]
    if env_name:
        return os.environ.get(str(env_name))
    return None


def _create_pairing(arguments: dict) -> dict:
    from omnidoer.omni_control.pairing import PairingStore, pairing_url, parse_duration_seconds, qr_text
    from omnidoer.omni_control.runtime import resolve_pairing_public_url

    public_url = resolve_pairing_public_url(str(arguments.get("public_url") or "") or None)
    expires = arguments.get("expires") or arguments.get("ttl") or "10m"
    pairing = PairingStore().create(public_url=public_url, ttl_seconds=parse_duration_seconds(expires))
    return {
        "status": "pairing_created",
        "pairing_url": pairing_url(pairing),
        "qr_ascii": qr_text(pairing),
        "expires_at": pairing.expires_at,
        "broker_fingerprint": pairing.broker_fingerprint,
        "web_broker_fingerprint": pairing.web_broker_fingerprint,
        "one_time_pairing": True,
        "paired_sessions_are_cached": True,
        "pairing_code_model_visible": True,
        "warning": "Only pair devices you control. Pairing URLs are one-time and short-lived.",
        "secret_exposed_to_model": False,
    }


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
        structured_details=_credential_structured_details(arguments),
    )
    if arguments.get("wait"):
        waited = _wait_for_control_request(
            {
                "request_id": request.request_id,
                "timeout": arguments.get("wait_timeout") or arguments.get("timeout") or "10m",
                "require_ciphertext": True,
            }
        )
        if waited.get("status") != "ok":
            return waited
        return {
            "status": "credential_response_received",
            "request": waited["request"],
            "notified": True,
            "has_ciphertext": waited["has_ciphertext"],
            "secret_exposed_to_model": False,
        }
    return {"status": "credential_request_created", "request": request.to_public_dict(), "secret_exposed_to_model": False}


def _wait_for_control_request(arguments: dict) -> dict:
    from omnidoer.omni_control.pairing import parse_duration_seconds
    from omnidoer.omni_control.requests import RequestStore, wait_for_request_completion

    request_id = arguments.get("request_id")
    if not request_id:
        return _error("error", "request_id required")
    try:
        request = wait_for_request_completion(
            str(request_id),
            timeout_seconds=parse_duration_seconds(arguments.get("timeout") or arguments.get("wait_timeout") or "10m"),
            require_ciphertext=bool(arguments.get("require_ciphertext")),
        )
    except KeyError:
        return {"status": "not_found", "secret_exposed_to_model": False}
    except TimeoutError:
        return {
            "status": "timeout",
            "request_id": str(request_id),
            "notified": False,
            "secret_exposed_to_model": False,
        }
    stored = RequestStore().get(str(request_id))
    return {
        "status": "ok",
        "request": stored.to_public_dict(),
        "notified": True,
        "completed_by_user": stored.completed_by_user,
        "has_ciphertext": stored.response_ciphertext is not None,
        "secret_exposed_to_model": False,
    }


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
        if request.used:
            return _error("rejected", "approval request already used")
        if request.status != "approved":
            return {
                "status": "approval_required",
                "request": request.to_public_dict(),
                "secret_exposed_to_model": False,
            }
        if origin and request.origin != origin:
            return _error("rejected", "file upload approval origin mismatch")
        store.consume_approval(request.request_id)
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


def _field_value(metadata: dict, *names: str) -> str:
    wanted = {name.lower() for name in names}
    fields = metadata.get("form_fields") if isinstance(metadata.get("form_fields"), list) else []
    for field in fields:
        if not isinstance(field, dict):
            continue
        keys = {str(field.get("name", "")).lower(), str(field.get("id", "")).lower()}
        if keys & wanted:
            return str(field.get("value") or "")
    return ""


def _approval_request_type(action_type: str) -> str:
    if action_type in {"payment_submit", "purchase", "transfer", "subscription"}:
        return "payment_approval"
    if action_type == "oauth_grant":
        return "oauth_approval"
    if action_type == "account_deletion":
        return "account_delete"
    if action_type == "send_sensitive_message":
        return "message_send"
    return "payment_approval"


def _sensitive_click_review(browser, selector: str, metadata: dict, action_type: str) -> tuple[str, str, str, dict]:
    from omnidoer.omni_policy.policy import origin_from_url

    origin = browser.current_origin() or ""
    top_level_url = browser.current_url()
    final_button = str(metadata.get("text") or metadata.get("value") or selector)
    form_action = str(metadata.get("form_action") or "")
    form_action_origin = origin_from_url(form_action) or ""
    structured_details = {
        "sensitive_action_type": action_type,
        "origin": origin,
        "form_action": form_action,
        "form_action_origin": form_action_origin,
        "final_button": final_button,
        "selector": selector,
        "merchant": _field_value(metadata, "merchant", "payee", "recipient"),
        "recipient": _field_value(metadata, "recipient", "payee", "merchant"),
        "amount": _field_value(metadata, "amount", "total"),
        "currency": _field_value(metadata, "currency"),
        "billing_method_summary": _field_value(metadata, "billing_method_summary", "payment_method_summary"),
        "subscription": _field_value(metadata, "subscription", "renewal"),
        "after_approval": f"Click '{final_button}' in the controlled browser only if these reviewed details are unchanged.",
    }
    action_summary = f"Approve {action_type.replace('_', ' ')}: {final_button}"
    return origin, top_level_url, action_summary, {key: value for key, value in structured_details.items() if value}


def _sensitive_click_allowed(arguments: dict, *, browser, selector: str) -> dict | None:
    from omnidoer.omni_approval.approval import approval_fingerprint, verify_approval_scope
    from omnidoer.omni_control.requests import RequestStore
    from omnidoer.omni_observer.redactor import redact_dom_snapshot
    from omnidoer.omni_policy.policy import classify_sensitive_click

    metadata = browser.click_target_metadata(selector)
    action_type = classify_sensitive_click(metadata)
    if not action_type:
        return None
    origin, top_level_url, action_summary, structured_details = _sensitive_click_review(browser, selector, metadata, action_type)
    store = RequestStore()
    request_id = arguments.get("approval_request_id") or arguments.get("request_id")
    if request_id:
        try:
            request = store.get(str(request_id))
        except KeyError:
            return _error("not_found", "approval request not found")
        if request.request_type != _approval_request_type(action_type):
            return _error("rejected", "approval request type does not match click action")
        try:
            request = verify_approval_scope(
                str(request_id),
                origin=origin,
                top_level_url=top_level_url,
                action_summary=action_summary,
                structured_details=structured_details,
                store=store,
                consume=True,
            )
        except PermissionError as exc:
            return {"status": "approval_scope_mismatch", "reason": str(exc), "secret_exposed_to_model": False}
        return None

    fingerprint = approval_fingerprint(
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        structured_details=structured_details,
    )
    request = store.create(
        _approval_request_type(action_type),
        origin=origin,
        top_level_url=top_level_url,
        action_summary=action_summary,
        risk_level=str(arguments.get("risk_level") or "high"),
        structured_details=redact_dom_snapshot(structured_details),
        approval_fingerprint=fingerprint,
    )
    return {
        "status": "approval_required",
        "request": request.to_public_dict(),
        "blocked_action": action_type,
        "secret_exposed_to_model": False,
    }


def _takeover_wait_timeout(arguments: dict) -> float:
    if "takeover_wait_timeout_seconds" in arguments:
        value = arguments.get("takeover_wait_timeout_seconds")
    else:
        value = os.environ.get("OMNIDOER_TAKEOVER_WAIT_TIMEOUT_SECONDS") or 600
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 600.0


def _active_browser_takeover(browser_context_id: str):
    from omnidoer.omni_control.requests import RequestStore

    for request in RequestStore().list():
        if (
            request.browser_context_id == browser_context_id
            and request.request_type in {"human_takeover", "account_registration"}
            and request.status == "user_control"
        ):
            return request
    return None


def _wait_for_browser_takeover_release(browser_context_id: str, *, timeout_seconds: float):
    import time

    deadline = time.time() + timeout_seconds
    request = _active_browser_takeover(browser_context_id)
    while request is not None and time.time() < deadline:
        time.sleep(0.25)
        request = _active_browser_takeover(browser_context_id)
    return request


def _pause_for_user_takeover_if_needed(arguments: dict, *, browser_context_id: str = "mcp-browser") -> dict | None:
    request = _wait_for_browser_takeover_release(
        browser_context_id,
        timeout_seconds=_takeover_wait_timeout(arguments),
    )
    if request is None:
        return None
    return {
        "status": "paused_for_human_takeover",
        "request": request.to_public_dict(),
        "agent_paused": True,
        "resume_after_user_releases_control": True,
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
            paused = _pause_for_user_takeover_if_needed(arguments)
            if paused is not None:
                return paused
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
                approval = _sensitive_click_allowed(arguments, browser=browser, selector=str(selector))
                if approval is not None:
                    return approval
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
        from omnidoer.omni_broker.broker import SecretBroker, validate_fill
        from omnidoer.omni_mcp.runtime import get_browser
        from omnidoer.omni_vault.vault import Vault

        browser = get_browser()
        current_url = browser.current_url()
        current_origin = browser.current_origin()
        if not current_origin:
            return _error("error", "active browser origin required")
        username_selector = str(
            arguments.get("username_selector")
            or "input[autocomplete='username'], input[name='email'], input[name='username'], input[name='acct'], #email, #username"
        )
        password_selector = str(arguments.get("password_selector") or "input[type='password']")
        request_id = arguments.get("request_id")
        if request_id:
            if name != "credential.fill_current_origin_login":
                return _error("unsupported", "request_id fill is only supported for login credentials")
            try:
                return SecretBroker().fill_after_receive(
                    str(request_id),
                    browser_controller=browser,
                    username_selector=username_selector,
                    password_selector=password_selector,
                )
            except PermissionError as exc:
                return {"status": "blocked", "reason": str(exc), "secret_exposed_to_model": False}
            except KeyError:
                return _error("not_found", "credential request not found")
            except ValueError as exc:
                return _error("unavailable", str(exc))
            except Exception as exc:
                return _error("unavailable", type(exc).__name__)
        try:
            passphrase = _vault_passphrase(arguments)
        except Exception as exc:
            return _error("locked", str(exc))
        if passphrase is None:
            return _error("locked", "passphrase_env or passphrase_file is required for vault-backed MCP fill")
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
    if name == "control.create_pairing":
        return _create_pairing(arguments)
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
    if name == "control.wait_request":
        return _wait_for_control_request(arguments or {})
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
    if name == "control.list_chat_messages":
        from omnidoer.omni_control.chat import ChatStore

        limit = int((arguments or {}).get("limit") or 200)
        return {
            "status": "ok",
            "messages": [message.to_public_dict() for message in ChatStore().list(limit=limit)],
            "records": [record.to_public_dict() for record in ChatStore().list_records(limit=limit)],
            "secret_exposed_to_model": False,
            "control_client_calls_model": False,
        }
    if name == "control.list_chat_records":
        from omnidoer.omni_control.chat import ChatStore

        limit = int((arguments or {}).get("limit") or 140)
        after = (arguments or {}).get("after_sequence")
        return {
            "status": "ok",
            "records": [
                record.to_public_dict()
                for record in ChatStore().list_records(limit=limit, after_sequence=int(after) if after is not None else None)
            ],
            "secret_exposed_to_model": False,
            "control_client_calls_model": False,
        }
    if name == "control.next_user_message":
        from omnidoer.omni_control.chat import ChatStore

        message = ChatStore().next_user_message(claim=True)
        if message is None:
            return {"status": "empty", "secret_exposed_to_model": False}
        return {"status": "ok", "message": message.to_public_dict(), "secret_exposed_to_model": False}
    if name == "control.publish_chat_message":
        from omnidoer.omni_control.chat import ChatStore

        message = ChatStore().append(
            role="assistant",
            text=str((arguments or {}).get("text") or ""),
            status=str((arguments or {}).get("status") or "completed"),
            source="agent",
            reply_to_message_id=str((arguments or {}).get("reply_to_message_id") or "") or None,
        )
        return {"status": "ok", "message": message.to_public_dict(), "secret_exposed_to_model": False}
    if name == "control.publish_chat_record":
        from omnidoer.omni_control.chat import ChatStore

        record = ChatStore().append_record(
            record_type=str((arguments or {}).get("record_type") or "note"),
            text=str((arguments or {}).get("text") or ""),
            role=str((arguments or {}).get("role") or "") or None,
            message_id=str((arguments or {}).get("message_id") or "") or None,
            source="agent",
            data=(arguments or {}).get("data") if isinstance((arguments or {}).get("data"), dict) else None,
        )
        return {"status": "ok", "record": record.to_public_dict(), "secret_exposed_to_model": False}
    if name == "control.append_chat_message_delta":
        from omnidoer.omni_control.chat import ChatStore

        message_id = str((arguments or {}).get("message_id") or "")
        delta = str((arguments or {}).get("delta") or "")
        if not message_id:
            return {"status": "error", "error": "message_id required", "secret_exposed_to_model": False}
        message = ChatStore().append_delta(message_id, delta)
        return {"status": "ok", "message": message.to_public_dict(), "secret_exposed_to_model": False}
    if name == "control.complete_chat_message":
        from omnidoer.omni_control.chat import ChatStore

        message_id = str((arguments or {}).get("message_id") or "")
        if not message_id:
            return {"status": "error", "error": "message_id required", "secret_exposed_to_model": False}
        text = (arguments or {}).get("text")
        message = ChatStore().complete(message_id, text=str(text) if text is not None else None)
        return {"status": "ok", "message": message.to_public_dict(), "secret_exposed_to_model": False}
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

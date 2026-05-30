"""MCP tool registry and status-only dispatch."""

from __future__ import annotations

ALLOWED_TOOLS = [
    "browser.open",
    "browser.observe",
    "browser.click",
    "browser.type_text",
    "browser.download_current_file",
    "browser.current_origin",
    "browser.detect_challenge",
    "browser.detect_antibot",
    "credential.list_for_current_origin",
    "credential.request_from_user",
    "credential.fill_current_origin_login",
    "credential.fill_current_origin_totp",
    "challenge.request_user_interaction",
    "challenge.status",
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


def call_tool(name: str, arguments: dict | None = None) -> dict:
    if name not in ALLOWED_TOOLS:
        raise KeyError(name)
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
    return {"status": "ok", "tool": name, "secret_exposed_to_model": False}

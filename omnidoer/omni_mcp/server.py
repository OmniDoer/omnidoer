"""Minimal MCP-compatible stdio server."""

from __future__ import annotations

import json
import sys


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
    "control.next_user_task",
]


def self_test() -> None:
    forbidden = {
        "captcha." + "solve",
        "captcha." + "bypass",
        "mfa." + "bypass",
        "antibot." + "bypass",
        "challenge." + "get_answer",
    }
    overlap = forbidden.intersection(ALLOWED_TOOLS)
    if overlap:
        raise RuntimeError(f"forbidden tools present: {sorted(overlap)}")


def serve_stdio() -> int:
    self_test()
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = request.get("method")
        response = {"jsonrpc": "2.0", "id": request.get("id")}
        if method == "initialize":
            response["result"] = {"protocolVersion": "2024-11-05", "serverInfo": {"name": "omnidoer", "version": "0.1.0"}}
        elif method == "tools/list":
            response["result"] = {"tools": [{"name": name, "description": f"OmniDoer action tool {name}", "inputSchema": {"type": "object"}} for name in ALLOWED_TOOLS]}
        elif method == "tools/call":
            name = (request.get("params") or {}).get("name")
            if name not in ALLOWED_TOOLS:
                response["error"] = {"code": -32601, "message": "tool not found"}
            else:
                response["result"] = {"content": [{"type": "text", "text": json.dumps({"status": "ok", "secret_exposed_to_model": False})}]}
        else:
            response["result"] = {}
        print(json.dumps(response), flush=True)
    return 0

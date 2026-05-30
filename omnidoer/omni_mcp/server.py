"""Minimal MCP-compatible stdio server."""

from __future__ import annotations

import json
import sys

from omnidoer.omni_mcp.tools import ALLOWED_TOOLS, call_tool, forbidden_tool_names, tool_descriptors


def self_test() -> None:
    overlap = forbidden_tool_names().intersection(ALLOWED_TOOLS)
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
            response["result"] = {"tools": tool_descriptors()}
        elif method == "tools/call":
            params = request.get("params") or {}
            name = params.get("name")
            if name not in ALLOWED_TOOLS:
                response["error"] = {"code": -32601, "message": "tool not found"}
            else:
                response["result"] = {"content": [{"type": "text", "text": json.dumps(call_tool(name, params.get("arguments") or {}))}]}
        else:
            response["result"] = {}
        print(json.dumps(response), flush=True)
    return 0

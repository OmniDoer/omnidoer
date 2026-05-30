"""Linux CLI/TUI control client commands."""

from __future__ import annotations

from omnidoer.omni_control.server import serve


def handle_control_command(args) -> int:
    command = args.control_command
    if command == "serve":
        serve(args.host, args.port)
        return 0
    if command == "status":
        print("OmniDoer Control Client: local mode")
        return 0
    if command == "tui":
        print("OmniDoer Control TUI: use control requests/approve/deny/input-secret for MVP CLI mode.")
        return 0
    if command == "requests":
        print("[]")
        return 0
    if command in {"approve", "deny", "input-secret", "challenge", "takeover", "release"}:
        print(f"{command}: request {args.request_id} is not available until request store is initialized")
        return 1
    return 0

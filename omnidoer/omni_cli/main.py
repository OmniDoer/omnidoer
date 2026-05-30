"""Command dispatcher for OmniDoer."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from omnidoer.paths import ensure_home


def _background(args: list[str]) -> int:
    ensure_home()
    log_path = ensure_home() / "background.log"
    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "omnidoer.omni_cli.main", *args],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    print(f"started background process pid={proc.pid} log={log_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omnidoer", description="OmniDoer local Codex sidecar runtime")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Check Codex auth mode and local runtime readiness")
    sub.add_parser("init", help="Create local OmniDoer state directory")

    demo = sub.add_parser("demo", help="Run the local demo site")
    demo_sub = demo.add_subparsers(dest="demo_command")
    demo_start = demo_sub.add_parser("start")
    demo_start.add_argument("--host", default="127.0.0.1")
    demo_start.add_argument("--port", type=int, default=8765)
    demo_start.add_argument("--background", action="store_true")

    control = sub.add_parser("control", help="Control Client commands")
    control_sub = control.add_subparsers(dest="control_command")
    serve = control_sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--background", action="store_true")
    control_sub.add_parser("tui")
    control_sub.add_parser("status")
    control_sub.add_parser("requests")
    submit_task = control_sub.add_parser("submit-task")
    submit_task.add_argument("task")
    control_sub.add_parser("tasks")
    for name in ("complete-task", "cancel-task"):
        p = control_sub.add_parser(name)
        p.add_argument("task_id")
    for name in ("approve", "deny", "input-secret", "challenge", "takeover", "release"):
        p = control_sub.add_parser(name)
        p.add_argument("request_id")

    vault = sub.add_parser("vault", help="Vault commands")
    vault_sub = vault.add_subparsers(dest="vault_command")
    vault_create = vault_sub.add_parser("create")
    vault_create.add_argument("--path", default=".omnidoer/vault.json")
    vault_create.add_argument("--passphrase-env")
    vault_unlock = vault_sub.add_parser("unlock")
    vault_unlock.add_argument("--path", default=".omnidoer/vault.json")
    vault_unlock.add_argument("--passphrase-env")

    cred = sub.add_parser("cred", help="Credential commands")
    cred_sub = cred.add_subparsers(dest="cred_command")
    cred_add = cred_sub.add_parser("add")
    cred_add.add_argument("--origin", required=True)
    cred_add.add_argument("--username", required=True)
    cred_add.add_argument("--vault", default=".omnidoer/vault.json")
    cred_add.add_argument("--passphrase-env")
    cred_sub.add_parser("list").add_argument("--vault", default=".omnidoer/vault.json")

    browser = sub.add_parser("browser", help="Browser commands")
    browser_sub = browser.add_subparsers(dest="browser_command")
    browser_open = browser_sub.add_parser("open")
    browser_open.add_argument("url")

    agent = sub.add_parser("agent", help="Run a demo OmniDoer agent task")
    agent_sub = agent.add_subparsers(dest="agent_command")
    run = agent_sub.add_parser("run")
    run.add_argument("task")
    run.add_argument("--vault", default=".omnidoer/vault.json")
    run.add_argument("--passphrase-env")
    run.add_argument("--demo-origin", default="http://127.0.0.1:8765")
    run.add_argument("--control-origin", default="http://127.0.0.1:8787")

    mcp = sub.add_parser("mcp", help="MCP server commands")
    mcp_sub = mcp.add_subparsers(dest="mcp_command")
    mcp_serve = mcp_sub.add_parser("serve")
    mcp_serve.add_argument("--self-test", action="store_true")

    audit = sub.add_parser("audit", help="Audit commands")
    audit_sub = audit.add_subparsers(dest="audit_command")
    audit_sub.add_parser("tail")
    audit_sub.add_parser("verify")

    policy = sub.add_parser("policy", help="Policy commands")
    policy_sub = policy.add_subparsers(dest="policy_command")
    policy_sub.add_parser("test")

    telegram = sub.add_parser("telegram", help="Telegram notification bridge")
    telegram_sub = telegram.add_subparsers(dest="telegram_command")
    telegram_sub.add_parser("status")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        from omnidoer.omni_cli.doctor import doctor_main

        return doctor_main()

    if args.command == "init":
        path = ensure_home()
        print(f"initialized OmniDoer local state at {path}")
        return 0

    if args.command == "demo" and args.demo_command == "start":
        if args.background:
            return _background(["demo", "start", "--host", args.host, "--port", str(args.port)])
        from omnidoer.demo.server import run_server

        run_server(args.host, args.port)
        return 0

    if args.command == "control":
        from omnidoer.omni_control.client_cli import handle_control_command

        if args.control_command == "serve" and args.background:
            return _background(["control", "serve", "--host", args.host, "--port", str(args.port)])
        return handle_control_command(args)

    if args.command == "vault":
        from omnidoer.omni_vault.vault import handle_vault_command

        return handle_vault_command(args)

    if args.command == "cred":
        from omnidoer.omni_broker.secret_requests import handle_cred_command

        return handle_cred_command(args)

    if args.command == "browser" and args.browser_command == "open":
        from omnidoer.omni_browser.controller import BrowserController

        with BrowserController() as browser:
            browser.open(args.url)
            print(browser.current_url())
        return 0

    if args.command == "agent" and args.agent_command == "run":
        from omnidoer.omni_agent.demo_agent import run_task

        return run_task(args)

    if args.command == "mcp" and args.mcp_command == "serve":
        from omnidoer.omni_mcp.server import serve_stdio, self_test

        if args.self_test:
            self_test()
            print("mcp self-test passed")
            return 0
        return serve_stdio()

    if args.command == "audit":
        from omnidoer.omni_audit.audit import handle_audit_command

        return handle_audit_command(args)

    if args.command == "policy" and args.policy_command == "test":
        from omnidoer.omni_policy.policy import policy_self_test

        policy_self_test()
        print("policy self-test passed")
        return 0

    if args.command == "telegram" and args.telegram_command == "status":
        from omnidoer.omni_telegram.bridge import status

        print(status())
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

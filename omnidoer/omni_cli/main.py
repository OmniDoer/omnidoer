"""Command dispatcher for OmniDoer."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from omnidoer.paths import ensure_home
from omnidoer.version import __version__


def _connect_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    if host == "localhost":
        return "127.0.0.1"
    return host


def _wait_for_tcp(host: str, port: int, proc: subprocess.Popen, *, timeout_seconds: float = 10.0) -> bool:
    deadline = time.time() + timeout_seconds
    connect_host = _connect_host(host)
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with socket.create_connection((connect_host, port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _background(args: list[str], *, wait_host: str | None = None, wait_port: int | None = None) -> int:
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
    if wait_host is not None and wait_port is not None and not _wait_for_tcp(wait_host, wait_port, proc):
        return_code = proc.poll()
        print(f"background process failed readiness pid={proc.pid} exit={return_code} log={log_path}", file=sys.stderr)
        return 1
    print(f"started background process pid={proc.pid} log={log_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omnidoer", description="OmniDoer local Codex sidecar runtime")
    parser.add_argument("--version", action="version", version=f"omnidoer {__version__}")
    sub = parser.add_subparsers(dest="command")

    console = sub.add_parser("console", help="Launch the OmniDoer-branded interactive console")
    console.add_argument("--dry-run", action="store_true")
    console.add_argument("codex_args", nargs=argparse.REMAINDER)
    sub.add_parser("doctor", help="Check Codex auth mode and local runtime readiness")
    sub.add_parser("init", help="Create local OmniDoer state directory")
    pair_top = sub.add_parser("pair", help="Create a Control Client pairing QR/code")
    pair_top.add_argument("--expires", default="10m")
    pair_top.add_argument("--public-url")
    pair_top.add_argument("--no-qr", action="store_true")
    upgrade = sub.add_parser("upgrade", help="Upgrade OmniDoer in-place from the GitHub checkout")
    upgrade.add_argument("--dry-run", action="store_true")
    upgrade.add_argument("--install-dir")
    upgrade.add_argument("--branch")

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
    serve.add_argument("--public-url")
    serve.add_argument("--cloud-direct", action="store_true")
    serve.add_argument("--tls-cert")
    serve.add_argument("--tls-key")
    serve.add_argument("--tls-self-signed-dev", action="store_true")
    serve.add_argument("--behind-reverse-proxy", action="store_true")
    serve.add_argument("--insecure-dev-public", action="store_true")
    serve.add_argument("--chat-runner", action="store_true")
    serve.add_argument("--chat-runner-interval", type=float, default=1.0)
    serve.add_argument("--chat-runner-cwd")
    serve.add_argument("--chat-codex-bin")
    serve.add_argument("--chat-thread-id")
    serve.add_argument("--chat-codex-arg", action="append", default=[])
    serve.add_argument("--chat-upload-ttl", default=None)
    serve.add_argument("--chat-allow-detached-thread-resume", action="store_true")
    serve.add_argument("--background", action="store_true")
    pair = control_sub.add_parser("pair")
    pair.add_argument("--print-qr", action="store_true")
    pair.add_argument("--expires", default="10m")
    pair.add_argument("--public-url")
    control_sub.add_parser("tui")
    control_sub.add_parser("status")
    control_sub.add_parser("requests")
    control_sub.add_parser("devices")
    revoke_device = control_sub.add_parser("revoke-device")
    revoke_device.add_argument("device_id")
    control_sub.add_parser("sessions")
    revoke_session = control_sub.add_parser("revoke-session")
    revoke_session.add_argument("session_id")
    control_sub.add_parser("tunnel-info")
    control_sub.add_parser("security-status")
    sync_status = control_sub.add_parser("sync-status")
    sync_status.add_argument("--thread-id")
    sync_status.add_argument("--codex-bin")
    wait_request = control_sub.add_parser("wait-request")
    wait_request.add_argument("request_id")
    wait_request.add_argument("--timeout", default="10m")
    submit_task = control_sub.add_parser("submit-task")
    submit_task.add_argument("task")
    control_sub.add_parser("tasks")
    for name in ("complete-task", "cancel-task"):
        p = control_sub.add_parser(name)
        p.add_argument("task_id")
    chat_send = control_sub.add_parser("chat-send")
    chat_send.add_argument("message")
    chat_log_user = control_sub.add_parser("chat-log-user")
    chat_log_user.add_argument("message")
    chat_log_user.add_argument("--source", default="tui_bridge")
    control_sub.add_parser("chat-messages")
    chat_next = control_sub.add_parser("chat-next")
    chat_next.add_argument("--no-claim", action="store_true")
    chat_reply = control_sub.add_parser("chat-reply")
    chat_reply.add_argument("message")
    chat_reply.add_argument("--reply-to")
    chat_record = control_sub.add_parser("chat-record")
    chat_record.add_argument("record_type")
    chat_record.add_argument("text")
    chat_record.add_argument("--role")
    chat_record.add_argument("--message-id")
    chat_start = control_sub.add_parser("chat-start")
    chat_start.add_argument("--reply-to")
    chat_start.add_argument("--source", default="control_cli")
    chat_delta = control_sub.add_parser("chat-delta")
    chat_delta.add_argument("message_id")
    chat_delta.add_argument("delta")
    chat_complete = control_sub.add_parser("chat-complete")
    chat_complete.add_argument("message_id")
    chat_complete.add_argument("--text")
    chat_run_next = control_sub.add_parser("chat-run-next")
    chat_run_next.add_argument("--codex-bin")
    chat_run_next.add_argument("--cwd")
    chat_run_next.add_argument("--thread-id")
    chat_run_next.add_argument("--codex-arg", action="append", default=[])
    chat_run_next.add_argument("--allow-detached-thread-resume", action="store_true")
    chat_runner = control_sub.add_parser("chat-runner")
    chat_runner.add_argument("--codex-bin")
    chat_runner.add_argument("--cwd")
    chat_runner.add_argument("--thread-id")
    chat_runner.add_argument("--codex-arg", action="append", default=[])
    chat_runner.add_argument("--interval", type=float, default=1.0)
    chat_runner.add_argument("--allow-detached-thread-resume", action="store_true")
    for name in ("approve", "deny", "input-secret", "challenge", "takeover", "release"):
        p = control_sub.add_parser(name)
        p.add_argument("request_id")

    vault = sub.add_parser("vault", help="Vault commands")
    vault_sub = vault.add_subparsers(dest="vault_command")
    vault_create = vault_sub.add_parser("create")
    vault_create.add_argument("--path", default=".omnidoer/vault.json")
    vault_create.add_argument("--passphrase-env")
    vault_create.add_argument("--passphrase-file")
    vault_unlock = vault_sub.add_parser("unlock")
    vault_unlock.add_argument("--path", default=".omnidoer/vault.json")
    vault_unlock.add_argument("--passphrase-env")
    vault_unlock.add_argument("--passphrase-file")

    cred = sub.add_parser("cred", help="Credential commands")
    cred_sub = cred.add_subparsers(dest="cred_command")
    cred_add = cred_sub.add_parser("add")
    cred_add.add_argument("--origin", required=True)
    cred_add.add_argument("--username", required=True)
    cred_add.add_argument("--vault", default=".omnidoer/vault.json")
    cred_add.add_argument("--passphrase-env")
    cred_add.add_argument("--passphrase-file")
    cred_request = cred_sub.add_parser("request")
    cred_request.add_argument("--origin", required=True)
    cred_request.add_argument("--top-level-url")
    cred_request.add_argument("--summary", default="Secure credential entry")
    cred_request.add_argument("--risk-level", default="low")
    cred_request.add_argument("--ttl", default="10m")
    cred_request.add_argument("--no-save-to-vault", action="store_true")
    cred_request.add_argument("--username-label")
    cred_request.add_argument("--password-label")
    cred_request.add_argument("--totp-label")
    cred_request.add_argument("--no-totp-field", action="store_true")
    cred_request.add_argument("--wait", action="store_true")
    cred_request.add_argument("--wait-timeout")
    cred_request.add_argument("--vault", default=".omnidoer/vault.json")
    cred_request.add_argument("--passphrase-env")
    cred_request.add_argument("--passphrase-file")
    cred_request.add_argument("--create-vault", action="store_true")
    cred_save_request = cred_sub.add_parser("save-request")
    cred_save_request.add_argument("request_id")
    cred_save_request.add_argument("--vault", default=".omnidoer/vault.json")
    cred_save_request.add_argument("--passphrase-env")
    cred_save_request.add_argument("--passphrase-file")
    cred_save_request.add_argument("--wait", action="store_true")
    cred_save_request.add_argument("--wait-timeout", default="10m")
    cred_save_request.add_argument("--create-vault", action="store_true")
    cred_sub.add_parser("list").add_argument("--vault", default=".omnidoer/vault.json")

    git = sub.add_parser("git", help="Vault-backed Git commands")
    git_sub = git.add_subparsers(dest="git_command")
    git_run = git_sub.add_parser("run")
    git_run.add_argument("--origin", default="https://github.com")
    git_run.add_argument("--vault", default=".omnidoer/vault.json")
    git_run.add_argument("--passphrase-env")
    git_run.add_argument("--passphrase-file")
    git_run.add_argument("--credential-id")
    git_run.add_argument("git_args", nargs=argparse.REMAINDER)
    git_askpass = git_sub.add_parser("_askpass", help=argparse.SUPPRESS)
    git_askpass.add_argument("prompt", nargs="?")

    github = sub.add_parser("github", help="Vault-backed GitHub API commands")
    github_sub = github.add_subparsers(dest="github_command")
    github_api = github_sub.add_parser("api")
    github_api.add_argument("method")
    github_api.add_argument("path")
    github_api.add_argument("--origin", default="https://github.com")
    github_api.add_argument("--api-origin", default="https://api.github.com")
    github_api.add_argument("--vault", default=".omnidoer/vault.json")
    github_api.add_argument("--passphrase-env")
    github_api.add_argument("--passphrase-file")
    github_api.add_argument("--credential-id")
    github_api.add_argument("--body-json")
    github_api.add_argument("--insecure-dev-api", action="store_true")

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
    run.add_argument("--passphrase-file")
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
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    sidecar_commands = {
        "agent",
        "audit",
        "browser",
        "console",
        "control",
        "cred",
        "demo",
        "doctor",
        "git",
        "github",
        "init",
        "mcp",
        "pair",
        "policy",
        "telegram",
        "upgrade",
        "vault",
    }
    if not raw_argv:
        from omnidoer.omni_cli.console import launch_codex_console

        return launch_codex_console([])
    first = raw_argv[0]
    if first == "console" and not (len(raw_argv) > 1 and raw_argv[1] in {"-h", "--help"}):
        from omnidoer.omni_cli.console import launch_codex_console

        console_args = raw_argv[1:]
        dry_run = False
        if console_args[:1] == ["--dry-run"]:
            dry_run = True
            console_args = console_args[1:]
        return launch_codex_console(console_args, dry_run=dry_run)
    if first.startswith("-") and first not in {"-h", "--help", "--version"}:
        from omnidoer.omni_cli.console import launch_codex_console

        return launch_codex_console(raw_argv)
    if not first.startswith("-") and first not in sidecar_commands:
        from omnidoer.omni_cli.console import launch_codex_console

        return launch_codex_console(raw_argv)

    parser = build_parser()
    args = parser.parse_args(raw_argv)

    if args.command == "console":
        from omnidoer.omni_cli.console import launch_codex_console

        return launch_codex_console(args.codex_args, dry_run=args.dry_run)

    if args.command == "doctor":
        from omnidoer.omni_cli.doctor import doctor_main

        return doctor_main()

    if args.command == "init":
        path = ensure_home()
        print(f"initialized OmniDoer local state at {path}")
        return 0

    if args.command == "upgrade":
        from omnidoer.omni_cli.upgrade import handle_upgrade_command

        return handle_upgrade_command(args)

    if args.command == "pair":
        from omnidoer.omni_control.client_cli import print_pairing_invite

        print_pairing_invite(public_url=args.public_url, expires=args.expires, print_qr=not args.no_qr)
        return 0

    if args.command == "demo" and args.demo_command == "start":
        if args.background:
            return _background(["demo", "start", "--host", args.host, "--port", str(args.port)], wait_host=args.host, wait_port=args.port)
        from omnidoer.demo.server import run_server

        run_server(args.host, args.port)
        return 0

    if args.command == "control":
        from omnidoer.omni_control.client_cli import handle_control_command

        if args.control_command == "serve" and args.background:
            from omnidoer.omni_control.cloud import build_config

            try:
                build_config(
                    host=args.host,
                    port=args.port,
                    public_url=args.public_url,
                    cloud_direct=args.cloud_direct,
                    tls_cert=args.tls_cert,
                    tls_key=args.tls_key,
                    tls_self_signed_dev=args.tls_self_signed_dev,
                    behind_reverse_proxy=args.behind_reverse_proxy,
                    insecure_dev_public=args.insecure_dev_public,
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            background_args = ["control", "serve", "--host", args.host, "--port", str(args.port)]
            for flag, value in (
                ("--public-url", args.public_url),
                ("--tls-cert", args.tls_cert),
                ("--tls-key", args.tls_key),
                ("--chat-runner-cwd", args.chat_runner_cwd),
                ("--chat-codex-bin", args.chat_codex_bin),
                ("--chat-thread-id", args.chat_thread_id),
                ("--chat-upload-ttl", args.chat_upload_ttl),
            ):
                if value:
                    background_args.extend([flag, value])
            if args.chat_runner_interval != 1.0:
                background_args.extend(["--chat-runner-interval", str(args.chat_runner_interval)])
            for value in args.chat_codex_arg:
                background_args.extend(["--chat-codex-arg", value])
            for flag, enabled in (
                ("--cloud-direct", args.cloud_direct),
                ("--tls-self-signed-dev", args.tls_self_signed_dev),
                ("--behind-reverse-proxy", args.behind_reverse_proxy),
                ("--insecure-dev-public", args.insecure_dev_public),
                ("--chat-runner", args.chat_runner),
                ("--chat-allow-detached-thread-resume", args.chat_allow_detached_thread_resume),
            ):
                if enabled:
                    background_args.append(flag)
            return _background(background_args, wait_host=args.host, wait_port=args.port)
        return handle_control_command(args)

    if args.command == "vault":
        from omnidoer.omni_vault.vault import handle_vault_command

        return handle_vault_command(args)

    if args.command == "cred":
        from omnidoer.omni_broker.secret_requests import handle_cred_command

        return handle_cred_command(args)

    if args.command == "git":
        from omnidoer.omni_vault.git_credentials import handle_git_command

        return handle_git_command(args)

    if args.command == "github":
        from omnidoer.omni_github.api import handle_github_command

        return handle_github_command(args)

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

"""Codex auth and local runtime diagnostics."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from omnidoer.paths import default_vault_path


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _run_codex_login_status() -> tuple[str, str]:
    codex = shutil.which("codex")
    if not codex:
        return "missing", "codex executable not found"
    try:
        result = subprocess.run(
            [codex, "login", "status"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostics
        return "error", f"failed to run codex login status: {type(exc).__name__}"

    output = result.stdout.strip()
    lowered = output.lower()
    if "chatgpt" in lowered:
        return "chatgpt", "OK: ChatGPT subscription-backed Codex auth detected."
    if "api key" in lowered or "apikey" in lowered or "openai_api_key" in lowered:
        return (
            "api_key",
            "WARNING: API-key billing mode detected. This uses OpenAI Platform API billing. If you want to use ChatGPT Pro subscription-backed Codex, run codex login and choose ChatGPT login.",
        )
    if result.returncode != 0:
        return "error", "codex login status returned a non-zero exit code"
    return "unknown", "Codex is installed, but auth mode could not be classified."


def _check_chromium() -> Check:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return Check(
            "chromium",
            "missing",
            "Python Playwright is not installed. Run python3 -m pip install -e '.[dev]' and python3 -m playwright install chromium.",
        )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:
        return Check(
            "chromium",
            "missing",
            f"Chromium could not be launched via Playwright: {type(exc).__name__}. Run python3 -m playwright install chromium.",
        )
    return Check("chromium", "ok", "Playwright Chromium launched successfully.")


def collect_checks() -> list[Check]:
    checks: list[Check] = []
    codex_path = shutil.which("codex")
    checks.append(Check("codex", "ok" if codex_path else "missing", codex_path or "not found"))

    mode, detail = _run_codex_login_status()
    checks.append(Check("codex_auth_mode", mode, detail))

    auth_path = Path.home() / ".codex" / "auth.json"
    checks.append(
        Check(
            "codex_auth_file",
            "present" if auth_path.exists() else "missing",
            "~/.codex/auth.json exists; contents were not read." if auth_path.exists() else "~/.codex/auth.json not found.",
        )
    )

    if "OPENAI_API_KEY" in os.environ:
        checks.append(
            Check(
                "openai_api_key",
                "set_not_used",
                "OPENAI_API_KEY is set, but OmniDoer will not use it by default.",
            )
        )
    else:
        checks.append(Check("openai_api_key", "unset", "OPENAI_API_KEY is not set; this is OK."))

    try:
        from omnidoer.omni_mcp.server import self_test

        self_test()
        checks.append(Check("mcp_server", "ok", "OmniDoer MCP self-test passed."))
    except Exception as exc:
        checks.append(Check("mcp_server", "error", f"MCP self-test failed: {type(exc).__name__}"))

    try:
        from omnidoer.omni_control.server import static_root

        index = static_root() / "index.html"
        checks.append(Check("control_client", "ok" if index.exists() else "missing", str(index)))
    except Exception as exc:
        checks.append(Check("control_client", "error", f"Control Client check failed: {type(exc).__name__}"))

    checks.append(_check_chromium())

    vault = default_vault_path()
    checks.append(Check("vault", "present" if vault.exists() else "missing", str(vault)))
    return checks


def doctor_main() -> int:
    for check in collect_checks():
        print(f"{check.name}: {check.status} - {check.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(doctor_main())

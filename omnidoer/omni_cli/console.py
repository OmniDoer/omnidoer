"""Launch the Codex TUI with OmniDoer branding and safe fallback paths."""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path


BRAND_ENV = {
    "OMNIDOER_CONSOLE": "1",
    "OMNIDOER_CLI_NAME": "omnidoer",
    "OMNIDOER_CODEX_BRAND": "omnidoer",
    "CODEX_CLI_BRAND": "omnidoer",
}


def infer_chat_thread_id(args: list[str]) -> str | None:
    """Infer the resumed Codex thread from interactive console arguments."""
    try:
        resume_index = args.index("resume")
    except ValueError:
        return None
    for value in args[resume_index + 1 :]:
        if value == "--":
            continue
        if value.startswith("-"):
            continue
        return value
    return None


def _path_candidates() -> list[str]:
    candidates: list[str] = []
    for env_name in ("OMNIDOER_CODEX_BIN", "OMNIDOER_REAL_CODEX"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(value)
    candidates.extend(
        [
            "/usr/local/lib/omnidoer/codex",
            "/usr/bin/codex",
            "/bin/codex",
        ]
    )
    found = shutil.which("codex")
    if found:
        candidates.append(found)
    return candidates


def find_codex_binary() -> str | None:
    seen: set[str] = set()
    for candidate in _path_candidates():
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        path = Path(candidate)
        # Avoid delegating back into the OmniDoer Codex shim and recursing.
        if path == Path("/usr/local/bin/codex") and not os.environ.get("OMNIDOER_CODEX_BIN"):
            continue
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def build_console_env(args: list[str] | None = None) -> dict[str, str]:
    from omnidoer.version import __version__

    env = os.environ.copy()
    env.update(BRAND_ENV)
    env["OMNIDOER_VERSION"] = __version__.lstrip("vV")
    env.setdefault("OMNIDOER_HOME", str(Path.home() / ".omnidoer"))
    env.setdefault("OMNIDOER_PYTHON", sys.executable)
    env.setdefault("OMNIDOER_INSTALL_DIR", str(Path(__file__).resolve().parents[2]))
    env.setdefault("OMNIDOER_TUI_CHAT_BRIDGE", "1")
    found_cli = shutil.which("omnidoer")
    if found_cli:
        env.setdefault("OMNIDOER_CLI", found_cli)
    thread_id = infer_chat_thread_id(args or [])
    if thread_id:
        env["OMNIDOER_CHAT_THREAD_ID"] = thread_id
    return env


def _print_startup_animation() -> None:
    if os.environ.get("OMNIDOER_DISABLE_SPLASH") == "1":
        return
    if not (sys.stdout.isatty() and sys.stderr.isatty()):
        return
    frames = [
        "[=     ] OmniDoer binding ChatGPT auth",
        "[===   ] OmniDoer mounting Control boundary",
        "[===== ] OmniDoer loading safe execution tools",
        "[======] OmniDoer console ready",
    ]
    width = max(len(frame) for frame in frames)
    print()
    print("    OMNIDOER")
    print("    Safe local agent console")
    for frame in frames:
        print(f"\r\033[2K>_ {frame:<{width}}", end="", flush=True)
        time.sleep(0.08)
    print()


def launch_codex_console(args: list[str], *, dry_run: bool = False) -> int:
    if not dry_run:
        from omnidoer.omni_cli.auto_upgrade import maybe_prompt_for_upgrade

        if maybe_prompt_for_upgrade():
            env = os.environ.copy()
            env["OMNIDOER_UPDATE_CHECK_SKIP_ONCE"] = "1"
            os.execvpe(sys.executable, [sys.executable, "-m", "omnidoer.omni_cli.main", *sys.argv[1:]], env)

    codex = find_codex_binary()
    if not codex:
        print("cannot launch OmniDoer console: Codex CLI binary was not found", file=sys.stderr)
        return 127

    env = build_console_env(args)
    argv = [codex, *args]
    if dry_run or os.environ.get("OMNIDOER_CONSOLE_DRY_RUN") == "1":
        print("OmniDoer console plan:")
        print(f"  binary={codex}")
        print(f"  argv={' '.join(argv)}")
        print("  brand=omnidoer")
        return 0

    _print_startup_animation()
    os.execvpe(codex, argv, env)
    return 127

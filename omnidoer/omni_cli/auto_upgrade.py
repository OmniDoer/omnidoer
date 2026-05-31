"""Interactive update checks for the OmniDoer console launcher."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import TextIO

from omnidoer.omni_cli.upgrade import _repo_root_from_package
from omnidoer.omni_cli.upgrade import handle_upgrade_command


_DISABLED_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class UpdateInfo:
    install_dir: Path
    branch: str
    local_revision: str
    remote_revision: str
    dirty: bool
    fast_forward: bool


def _env_disabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _DISABLED_VALUES


def _upgrade_check_timeout() -> float:
    raw_value = os.environ.get("OMNIDOER_UPDATE_CHECK_TIMEOUT", "8")
    try:
        return max(1.0, float(raw_value))
    except ValueError:
        return 8.0


def _git(
    install_dir: Path,
    args: list[str],
    *,
    timeout: float,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(install_dir), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return result


def _default_install_dir() -> Path:
    return Path(os.environ.get("OMNIDOER_INSTALL_DIR") or _repo_root_from_package()).expanduser().resolve()


def check_for_update(
    install_dir: Path | None = None,
    branch: str | None = None,
    *,
    timeout: float | None = None,
) -> UpdateInfo | None:
    install_dir = (install_dir or _default_install_dir()).expanduser().resolve()
    branch = branch or os.environ.get("OMNIDOER_BRANCH") or "main"
    timeout = timeout if timeout is not None else _upgrade_check_timeout()

    if not (install_dir / ".git").is_dir():
        return None

    _git(install_dir, ["fetch", "--quiet", "origin", branch], timeout=timeout)
    local_revision = _git(install_dir, ["rev-parse", "HEAD"], timeout=timeout).stdout.strip()
    remote_revision = _git(install_dir, ["rev-parse", f"origin/{branch}"], timeout=timeout).stdout.strip()
    if not local_revision or not remote_revision or local_revision == remote_revision:
        return None

    dirty = bool(_git(install_dir, ["status", "--porcelain"], timeout=timeout).stdout.strip())
    fast_forward = (
        _git(
            install_dir,
            ["merge-base", "--is-ancestor", local_revision, remote_revision],
            timeout=timeout,
            check=False,
        ).returncode
        == 0
    )
    return UpdateInfo(
        install_dir=install_dir,
        branch=branch,
        local_revision=local_revision,
        remote_revision=remote_revision,
        dirty=dirty,
        fast_forward=fast_forward,
    )


def _short_revision(revision: str) -> str:
    return revision[:10]


def _is_yes(answer: str) -> bool:
    return answer.strip().lower() in {"y", "yes", "是", "好", "确认", "升级"}


def _is_interactive(stdout: TextIO) -> bool:
    return sys.stdin.isatty() and stdout.isatty()


def maybe_prompt_for_upgrade(
    *,
    input_func: Callable[[str], str] = input,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    is_interactive: Callable[[], bool] | None = None,
) -> bool:
    if _env_disabled("OMNIDOER_UPDATE_CHECK") or os.environ.get("OMNIDOER_UPDATE_CHECK_SKIP_ONCE") == "1":
        return False
    if is_interactive is None:
        is_interactive = lambda: _is_interactive(stdout)
    if not is_interactive():
        return False

    try:
        update = check_for_update()
    except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
        if os.environ.get("OMNIDOER_UPDATE_CHECK_VERBOSE") == "1":
            print(f"OmniDoer update check skipped: {exc}", file=stderr)
        return False

    if update is None:
        return False

    if not update.fast_forward:
        print(
            f"OmniDoer update check found origin/{update.branch}, but {update.install_dir} "
            "cannot fast-forward to it.",
            file=stderr,
        )
        return False

    print(
        "OmniDoer update available: "
        f"{_short_revision(update.local_revision)} -> {_short_revision(update.remote_revision)} "
        f"(origin/{update.branch})",
        file=stdout,
    )
    if update.dirty:
        print(
            f"Update prompt skipped because {update.install_dir} has local changes. "
            "Run `omnidoer upgrade` after committing or stashing them.",
            file=stderr,
        )
        return False

    try:
        answer = input_func("Upgrade now before launching the console? [y/N] ")
    except (EOFError, KeyboardInterrupt):
        print(file=stdout)
        return False
    if not _is_yes(answer):
        print("Continuing with the installed OmniDoer version.", file=stdout)
        return False

    args = argparse.Namespace(
        dry_run=False,
        install_dir=str(update.install_dir),
        branch=update.branch,
    )
    exit_code = handle_upgrade_command(args)
    if exit_code != 0:
        print("OmniDoer upgrade did not complete; launching the installed version.", file=stderr)
        return False
    return True

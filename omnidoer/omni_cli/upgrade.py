"""Self-upgrade support for installations created by the OmniDoer installer."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _repo_root_from_package() -> Path:
    return Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _is_dirty(install_dir: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(install_dir), "status", "--porcelain"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


def _print_plan(install_dir: Path, branch: str) -> None:
    print("OmniDoer upgrade plan:")
    print(f"  install_dir={install_dir}")
    print(f"  branch={branch}")
    print(f"  python={sys.executable}")
    print(f"  git -C {install_dir} fetch origin {branch}")
    print(f"  git -C {install_dir} checkout {branch}")
    print(f"  git -C {install_dir} pull --ff-only origin {branch}")
    print(f"  {sys.executable} -m pip install -e {install_dir}[dev]")


def handle_upgrade_command(args: argparse.Namespace) -> int:
    install_dir = Path(
        args.install_dir
        or os.environ.get("OMNIDOER_INSTALL_DIR")
        or _repo_root_from_package()
    ).expanduser().resolve()
    branch = args.branch or os.environ.get("OMNIDOER_BRANCH") or "main"

    if args.dry_run:
        _print_plan(install_dir, branch)
        return 0

    if not (install_dir / ".git").is_dir():
        print(f"cannot upgrade: {install_dir} is not a git checkout", file=sys.stderr)
        print("Install with omnidoer/scripts/install-cloud-direct.sh or pass --install-dir.", file=sys.stderr)
        return 2

    try:
        if _is_dirty(install_dir):
            print(f"cannot upgrade: {install_dir} has uncommitted changes", file=sys.stderr)
            print("Commit, stash, or use a clean install directory before upgrading.", file=sys.stderr)
            return 2
        _run(["git", "-C", str(install_dir), "fetch", "origin", branch])
        _run(["git", "-C", str(install_dir), "checkout", branch])
        _run(["git", "-C", str(install_dir), "pull", "--ff-only", "origin", branch])
        _run([sys.executable, "-m", "pip", "install", "-e", f"{install_dir}[dev]"])
    except subprocess.CalledProcessError as exc:
        print(f"upgrade failed: {exc}", file=sys.stderr)
        return exc.returncode or 1

    print(f"OmniDoer upgraded from origin/{branch} at {install_dir}")
    return 0


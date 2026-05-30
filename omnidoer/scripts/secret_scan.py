"""Small repository guard for obviously unsafe secret interfaces."""

from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCAN_ROOTS = [ROOT / "omnidoer"]
FORBIDDEN_NAMES = {
    "get_password",
    "decrypt_password",
    "get_totp_code",
    "get_cookie",
    "get_api_key",
    "export_secret",
    "print_secret",
    "copy_secret_to_clipboard",
    "dump_cookies",
    "dump_local_storage",
    "dump_password_values",
    "read_private_key",
    "export_private_key",
}
TOKEN_PATTERNS = [
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
]
SKIP_DIRS = {".git", "target", "node_modules", ".venv"}


def iter_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for root in SCAN_ROOTS:
        try:
            paths = list(root.rglob("*"))
        except FileNotFoundError:
            continue
        for path in paths:
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            files.append(path)
    return files


def main() -> int:
    failures: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError):
            continue
        lowered = text.lower()
        if path.name != "secret_scan.py":
            for name in FORBIDDEN_NAMES:
                if name in lowered:
                    failures.append(f"{path.relative_to(ROOT)} contains forbidden interface {name}")
        for pattern in TOKEN_PATTERNS:
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)} appears to contain a GitHub token")

    if failures:
        print("\n".join(failures))
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

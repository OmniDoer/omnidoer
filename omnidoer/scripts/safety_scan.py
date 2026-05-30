"""OmniDoer repository safety gate.

This scan complements unit tests. It checks code-level invariants that should
stay true even as individual tests move around:

- no default OpenAI API client path in OmniDoer code;
- no forbidden bypass/secret-returning MCP tools in the registry;
- no forbidden bypass tool names in model-visible code;
- localized README posters and Control Client release docs remain wired.
"""

from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
CODE_ROOTS = [ROOT / "omnidoer", ROOT / "tests"]
TEXT_FILES = {".py", ".js", ".ts", ".md", ".yml", ".yaml", ".toml", ".html", ".css", ".json"}
SKIP_DIRS = {".git", "__pycache__", "target", "node_modules", ".venv"}


def _join(*parts: str) -> str:
    return "".join(parts)


DEFAULT_MODEL_PATTERNS = [
    re.compile(_join("from ", "openai ", "import")),
    re.compile(_join(r"\b", "OpenAI", r"\s*\(")),
    re.compile(_join("responses", ".create", r"\s*\("), re.IGNORECASE),
    re.compile(_join("chat", ".completions", ".create", r"\s*\("), re.IGNORECASE),
]

FORBIDDEN_TOOL_NAMES = {
    _join("credential.", "get_", "password"),
    _join("credential.", "decrypt"),
    _join("credential.", "get_", "totp"),
    _join("credential.", "get_", "cookie"),
    _join("vault.", "export"),
    _join("browser.", "dump_", "cookies"),
    _join("browser.", "dump_local_", "storage"),
    _join("browser.", "dump_", "password_values"),
    _join("secret.", "read"),
    _join("secret.", "print"),
    _join("secret.", "copy_to_clipboard"),
    _join("captcha.", "solve"),
    _join("captcha.", "bypass"),
    _join("mfa.", "bypass"),
    _join("antibot.", "bypass"),
    _join("challenge.", "get_answer"),
    _join("takeover.", "get_user_input"),
}


def iter_text_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for root in CODE_ROOTS:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_FILES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            files.append(path)
    return files


def scan_default_model_paths(failures: list[str]) -> None:
    for path in iter_text_files():
        if path.name == "safety_scan.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in DEFAULT_MODEL_PATTERNS:
            if pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)} appears to contain a default OpenAI API client path")


def scan_forbidden_tool_registry(failures: list[str]) -> None:
    from omnidoer.omni_mcp.tools import ALLOWED_TOOLS, forbidden_tool_names

    overlap = set(ALLOWED_TOOLS).intersection(forbidden_tool_names())
    overlap.update(set(ALLOWED_TOOLS).intersection(FORBIDDEN_TOOL_NAMES))
    if overlap:
        failures.append(f"forbidden MCP tools registered: {sorted(overlap)}")


def scan_forbidden_tool_mentions(failures: list[str]) -> None:
    allowed_files = {
        pathlib.Path("omnidoer/scripts/safety_scan.py"),
        pathlib.Path("omnidoer/omni_mcp/tools.py"),
    }
    for path in iter_text_files():
        rel = path.relative_to(ROOT)
        if rel in allowed_files:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in FORBIDDEN_TOOL_NAMES:
            if name in text:
                failures.append(f"{rel} contains forbidden tool name {name}")


def scan_public_branding_contract(failures: list[str]) -> None:
    languages = ("en", "zh-CN", "es", "fr", "de", "ja", "ko")
    for lang in languages:
        image = ROOT / "docs" / "assets" / "localized" / f"omnidoer-readme-{lang}.jpg"
        if not image.is_file():
            failures.append(f"missing localized README poster: {image.relative_to(ROOT)}")
    release_doc = ROOT / "docs" / "control-client-release.md"
    if release_doc.is_file():
        text = release_doc.read_text(encoding="utf-8", errors="ignore")
        if "omnidoer-control-client-pwa.zip" not in text:
            failures.append("control-client release docs do not mention the PWA zip asset")


def main() -> int:
    failures: list[str] = []
    scan_default_model_paths(failures)
    scan_forbidden_tool_registry(failures)
    scan_forbidden_tool_mentions(failures)
    scan_public_branding_contract(failures)
    if failures:
        print("\n".join(failures))
        return 1
    print("safety scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

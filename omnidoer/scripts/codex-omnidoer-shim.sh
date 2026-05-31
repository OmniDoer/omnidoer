#!/usr/bin/env sh
set -eu

real_codex="${OMNIDOER_REAL_CODEX:-/usr/bin/codex}"
omnidoer_cli="${OMNIDOER_CLI:-$(command -v omnidoer 2>/dev/null || true)}"

if [ "${1:-}" = "omnidoer" ]; then
  shift
  if [ -z "$omnidoer_cli" ]; then
    echo "omnidoer CLI not found on PATH; set OMNIDOER_CLI" >&2
    exit 127
  fi
  exec "$omnidoer_cli" "$@"
fi

if [ ! -x "$real_codex" ]; then
  echo "real Codex CLI not found at $real_codex; set OMNIDOER_REAL_CODEX" >&2
  exit 127
fi

if [ "${OMNIDOER_CODEX_MCP_AUTO_REGISTER:-1}" = "1" ] && [ -n "$omnidoer_cli" ]; then
  codex_config="${CODEX_HOME:-$HOME/.codex}/config.toml"
  if ! { [ -f "$codex_config" ] && grep -q "omnidoer" "$codex_config"; }; then
    "$real_codex" mcp add omnidoer -- "$omnidoer_cli" mcp serve >/dev/null 2>&1 || true
  fi
fi

exec "$real_codex" "$@"


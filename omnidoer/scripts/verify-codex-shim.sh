#!/usr/bin/env sh
set -eu

shim_path="${OMNIDOER_CODEX_SHIM_PATH:-/usr/local/bin/codex}"
real_codex="${OMNIDOER_REAL_CODEX:-/usr/bin/codex}"

if [ "$(command -v codex)" != "$shim_path" ]; then
  echo "codex does not resolve to shim: $(command -v codex)" >&2
  exit 1
fi

codex_version="$(codex --version)"
case "$codex_version" in
  codex-cli\ *) ;;
  *)
    echo "unexpected codex --version output: $codex_version" >&2
    exit 1
    ;;
esac

if ! codex omnidoer --version | grep -Eq '^omnidoer v20[0-9]{12}$'; then
  echo "codex omnidoer --version failed" >&2
  exit 1
fi

if ! codex omnidoer mcp serve --self-test | grep -q 'mcp self-test passed'; then
  echo "OmniDoer MCP self-test through codex shim failed" >&2
  exit 1
fi

if ! codex mcp list | grep -q '^omnidoer'; then
  echo "OmniDoer MCP server is not registered in Codex" >&2
  exit 1
fi

if [ ! -x "$real_codex" ]; then
  echo "real Codex CLI missing at $real_codex" >&2
  exit 1
fi

echo "codex shim verified"
echo "shim=$shim_path"
echo "real_codex=$real_codex"
echo "codex_version=$codex_version"


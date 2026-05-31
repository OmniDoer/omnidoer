#!/usr/bin/env sh
set -eu

target="${OMNIDOER_CODEX_SHIM_PATH:-/usr/local/bin/codex}"

if [ ! -e "$target" ]; then
  echo "no OmniDoer Codex shim found at $target"
  exit 0
fi

if [ "$(id -u)" = "0" ]; then
  rm -f "$target"
elif command -v sudo >/dev/null 2>&1; then
  sudo rm -f "$target"
else
  echo "removing $target requires root or sudo" >&2
  exit 1
fi

echo "removed OmniDoer Codex shim at $target"
echo "codex now resolves to the next binary on PATH"


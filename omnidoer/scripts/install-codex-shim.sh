#!/usr/bin/env sh
set -eu

target="${OMNIDOER_CODEX_SHIM_PATH:-/usr/local/bin/codex}"
source_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
source_file="$source_dir/codex-omnidoer-shim.sh"

if [ ! -f "$source_file" ]; then
  echo "missing shim source: $source_file" >&2
  exit 1
fi

if [ "$(id -u)" = "0" ]; then
  install -m 0755 "$source_file" "$target"
elif command -v sudo >/dev/null 2>&1; then
  sudo install -m 0755 "$source_file" "$target"
else
  echo "installing $target requires root or sudo" >&2
  exit 1
fi

echo "installed OmniDoer Codex shim at $target"
echo "rollback: rm -f $target"


#!/usr/bin/env sh
set -eu

source_path="${1:-${OMNIDOER_NATIVE_CONSOLE_BIN:-}}"
target="${OMNIDOER_NATIVE_CONSOLE_TARGET:-/usr/local/lib/omnidoer/codex}"

if [ -z "$source_path" ]; then
  echo "usage: install-native-console.sh /path/to/omnidoer-codex-linux-x64" >&2
  exit 2
fi

if [ ! -f "$source_path" ]; then
  echo "native console binary not found: $source_path" >&2
  exit 1
fi

install_cmd="install -D -m 0755"
if [ "$(id -u)" = "0" ]; then
  $install_cmd "$source_path" "$target"
elif command -v sudo >/dev/null 2>&1; then
  sudo $install_cmd "$source_path" "$target"
else
  echo "installing $target requires root or sudo" >&2
  exit 1
fi

echo "installed OmniDoer native console at $target"
echo "rollback: rm -f $target"

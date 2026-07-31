#!/usr/bin/env sh
set -eu

source_path="${1:-${OMNIDOER_MOONBRIDGE_BIN:-}}"
target="${OMNIDOER_MOONBRIDGE_TARGET:-/usr/local/lib/omnidoer/moonbridge}"
template_path="${OMNIDOER_MOONBRIDGE_TEMPLATE:-/etc/omnidoer/moonbridge-deepseek.yml.template}"
unit_path="${OMNIDOER_MOONBRIDGE_UNIT:-/etc/systemd/system/omnidoer-moonbridge.service}"
user_home=$(getent passwd "$(id -u)" | cut -d: -f6)
codex_config="${OMNIDOER_CODEX_CONFIG:-$user_home/.codex/config.toml}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
template_dir=$(dirname -- "$script_dir")/deepseek

if [ -z "$source_path" ]; then
  echo "usage: install-deepseek-bridge.sh /path/to/omnidoer-moonbridge-linux-x64" >&2
  exit 2
fi

if [ ! -f "$source_path" ]; then
  echo "Moon Bridge binary not found: $source_path" >&2
  exit 1
fi

if [ "$(id -u)" != "0" ]; then
  echo "installing the DeepSeek bridge requires root" >&2
  exit 1
fi

install -D -m 0755 "$source_path" "$target"
install -d -m 0755 "$(dirname -- "$template_path")" /var/lib/omnidoer-moonbridge
install -m 0644 "$template_dir/moonbridge.yml.template" "$template_path"
install -m 0644 "$template_dir/omnidoer-moonbridge.service" "$unit_path"
install -d -m 0700 "$(dirname -- "$codex_config")"
touch "$codex_config"
chmod 0600 "$codex_config"
if ! grep -Fq '[model_providers.deepseek]' "$codex_config"; then
  {
    echo
    echo '[model_providers.deepseek]'
    echo 'name = "DeepSeek V4 via Moon Bridge"'
    echo 'base_url = "http://127.0.0.1:38440/v1"'
    echo 'wire_api = "responses"'
    echo 'requires_openai_auth = false'
  } >>"$codex_config"
fi
systemctl daemon-reload
systemctl enable omnidoer-moonbridge.service
if omnidoer provider deepseek prepare-runtime >/dev/null 2>&1; then
  systemctl restart omnidoer-moonbridge.service
else
  echo "DeepSeek bridge installed but waiting for an API key from OmniDoer Control Client"
fi

echo "installed OmniDoer DeepSeek bridge at $target"
echo "configuration template: $template_path"
echo "Codex provider configuration: $codex_config"
echo "the API key remains encrypted in OmniDoer Vault and is materialized only under /run"

#!/usr/bin/env sh
set -eu

repo="${OMNIDOER_REPO:-https://github.com/OmniDoer/omnidoer.git}"
branch="${OMNIDOER_BRANCH:-main}"
install_dir="${OMNIDOER_INSTALL_DIR:-$HOME/omnidoer}"
venv_dir="${OMNIDOER_VENV_DIR:-$install_dir/.venv}"
host="${OMNIDOER_HOST:-127.0.0.1}"
port="${OMNIDOER_PORT:-8787}"
cloud_direct="${OMNIDOER_CLOUD_DIRECT:-0}"
public_url="${OMNIDOER_PUBLIC_URL:-}"
start_service="${OMNIDOER_START:-1}"
register_mcp="${OMNIDOER_REGISTER_MCP:-1}"
playwright_deps="${OMNIDOER_WITH_BROWSER_DEPS:-auto}"
replace_codex="${OMNIDOER_REPLACE_CODEX:-0}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 is required. Install it first, then run this installer again." >&2
    exit 1
  fi
}

need git
need python3

if [ "$cloud_direct" = "1" ]; then
  host="${OMNIDOER_HOST:-0.0.0.0}"
  if [ -z "$public_url" ]; then
    echo "OMNIDOER_PUBLIC_URL is required when OMNIDOER_CLOUD_DIRECT=1." >&2
    echo "Example: curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com bash" >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "$install_dir")"
if [ -d "$install_dir/.git" ]; then
  git -C "$install_dir" fetch origin "$branch"
  git -C "$install_dir" checkout "$branch"
  git -C "$install_dir" pull --ff-only origin "$branch"
else
  git clone --branch "$branch" "$repo" "$install_dir"
fi

python3 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install --upgrade pip
"$venv_dir/bin/python" -m pip install -e "${install_dir}[dev]"

if [ "${OMNIDOER_SKIP_PLAYWRIGHT:-0}" != "1" ]; then
  if [ "$playwright_deps" = "1" ] || { [ "$playwright_deps" = "auto" ] && { [ "$(id -u)" = "0" ] || command -v sudo >/dev/null 2>&1; }; }; then
    "$venv_dir/bin/python" -m playwright install --with-deps chromium || "$venv_dir/bin/python" -m playwright install chromium
  else
    "$venv_dir/bin/python" -m playwright install chromium
  fi
fi

"$venv_dir/bin/omnidoer" init
"$venv_dir/bin/omnidoer" doctor || true
"$venv_dir/bin/omnidoer" mcp serve --self-test

if [ "$register_mcp" = "1" ] && command -v codex >/dev/null 2>&1; then
  codex mcp add omnidoer -- "$venv_dir/bin/omnidoer" mcp serve || true
fi

if [ "$replace_codex" = "1" ]; then
  if [ "$(id -u)" = "0" ]; then
    install -m 0755 "$install_dir/omnidoer/scripts/codex-omnidoer-shim.sh" /usr/local/bin/codex
  elif command -v sudo >/dev/null 2>&1; then
    sudo install -m 0755 "$install_dir/omnidoer/scripts/codex-omnidoer-shim.sh" /usr/local/bin/codex
  else
    echo "OMNIDOER_REPLACE_CODEX=1 requires root or sudo to write /usr/local/bin/codex." >&2
    exit 1
  fi
  echo "Installed OmniDoer Codex shim at /usr/local/bin/codex"
fi

if [ "$start_service" = "1" ]; then
  if [ "$cloud_direct" = "1" ]; then
    "$venv_dir/bin/omnidoer" control serve \
      --cloud-direct \
      --host "$host" \
      --port "$port" \
      --public-url "$public_url" \
      --behind-reverse-proxy \
      --background
    echo "OmniDoer Control Service requested at $public_url"
  else
    "$venv_dir/bin/omnidoer" control serve --host "$host" --port "$port" --background
    echo "OmniDoer Control Service requested at http://$host:$port/"
  fi
fi

echo
echo "Installed OmniDoer at: $install_dir"
echo "CLI: $venv_dir/bin/omnidoer"
echo "Create a pairing QR/code:"
if [ "$cloud_direct" = "1" ]; then
  echo "  $venv_dir/bin/omnidoer control pair --print-qr --public-url $public_url"
else
  echo "  $venv_dir/bin/omnidoer control pair --print-qr"
fi
echo "Submit a task:"
echo "  $venv_dir/bin/omnidoer control submit-task \"Use OmniDoer on the local demo\""
echo "Upgrade later:"
echo "  $venv_dir/bin/omnidoer upgrade"
echo "Optional Codex shim:"
echo "  curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | OMNIDOER_REPLACE_CODEX=1 sh"

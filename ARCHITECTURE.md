# Architecture

OmniDoer is an upstream-friendly Codex CLI fork with a local sidecar runtime.
The preferred integration path is MCP, so Codex can request browser actions and
credential use without receiving secrets.

## Components

- `omni-vault`: encrypted local credential store using Argon2id and an AEAD such as XChaCha20-Poly1305 or AES-256-GCM.
- `omni-broker`: Unix-domain-socket Secret Broker that validates origin, frame, form-action, and policy before using a secret.
- `omni-browser`: Linux headless Chromium controller using Playwright or CDP.
- `omni-observer`: redaction layer for DOM, accessibility, network summaries, screenshots, and logs.
- `omni-mcp`: MCP server exposing only safe action tools.
- `omni-approval`: human confirmation system for sensitive actions.
- `omni-telegram`: optional low-sensitivity notification and approval bridge, disabled by default.
- `omni-audit`: hash-chained audit log without secrets.
- `omni-policy`: TOML or YAML policy engine.
- `omni-cli`: developer and user command surface.

## Data Flow

1. The model asks for an action such as credential fill.
2. The MCP server sends the request to the broker.
3. The broker asks the browser controller for current URL, origin, frame tree, field metadata, and form action.
4. The broker checks vault metadata and policy.
5. The vault decrypts only inside the broker-controlled path.
6. The broker injects into the browser field.
7. The broker returns status only.
8. The observer redacts page state before the model sees it.

## Upstream Strategy

Codex CLI core should stay easy to rebase. OmniDoer code should live in
sidecar crates, MCP servers, plugins, or narrow integration hooks. Broad
changes to `codex-rs/core` should be avoided unless there is no stable sidecar
route.

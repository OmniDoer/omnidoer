# Branch Strategy

- `main` is the stable OmniDoer branch.
- `omnidoer-mvp` is the current development branch for the first runnable MVP.
- `upstream/main` is `openai/codex`.

Sync strategy:

```sh
git fetch upstream
git checkout main
git merge upstream/main
```

Keep OmniDoer changes in sidecar, MCP, Control Client, Vault, Broker, Challenge
Relay, Human Takeover Relay, Approval, Audit, and demo modules. Do not modify
Codex auth, billing, token refresh, or model provider logic.

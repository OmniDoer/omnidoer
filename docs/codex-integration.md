# Codex Integration

OmniDoer is a Codex CLI sidecar. It does not implement a new model provider,
does not create an OpenAI API client, and does not require `OPENAI_API_KEY`.

Use MCP:

```sh
codex mcp add omnidoer -- omnidoer mcp serve
```

Codex remains responsible for authentication, billing, token refresh, and
model provider selection. `omnidoer doctor` only checks Codex status; it does
not read `~/.codex/auth.json` contents and does not modify Codex auth storage.

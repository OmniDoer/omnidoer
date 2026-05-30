# Codex Integration

OmniDoer is a Codex CLI sidecar. It does not implement a new model provider,
does not create an OpenAI API client, and does not require `OPENAI_API_KEY`.

Use MCP:

```sh
codex mcp add omnidoer -- omnidoer mcp serve
```

Control Client initiated work uses a local queue:

```sh
omnidoer control submit-task "登录 demo 网站并下载我的发票"
```

Codex can claim the next queued task with the MCP tool
`control.next_user_task`. The Control Client never calls models directly and
does not introduce a second billing path.

Codex remains responsible for authentication, billing, token refresh, and
model provider selection. `omnidoer doctor` only checks Codex status; it does
not read `~/.codex/auth.json` contents and does not modify Codex auth storage.

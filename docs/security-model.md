# Security Model

The model is not a security boundary.

Security boundaries:

- Codex CLI remains the only model/agent inference entry.
- OmniDoer tools run as local MCP/sidecar actions.
- Secret Broker validates origin and policy before credential use.
- Vault encrypts secret payloads with Argon2id-derived keys and AES-GCM.
- Control Client sends secrets and challenge responses through the secure channel.
- Challenge Relay never returns answers.
- Human Takeover never returns user input.
- Audit log is hash-chained and redacted.

`OPENAI_API_KEY` is not required by OmniDoer and is not used by default.

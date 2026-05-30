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
- Error and exception fields are treated as sensitive surfaces because browser,
  challenge, or takeover failures may otherwise echo user input.

Operational rule:

- The Agent can request action.
- The Broker and policy layer decide whether the request is scoped and allowed.
- The Vault releases only credential use, not credential value.
- Human challenge, registration, passkey, and anti-bot interactions stay in the
  Control Client takeover path.
- Final payments, OAuth grants, account changes, uploads, and message sends
  require scoped human approval that is consumed before release.

`OPENAI_API_KEY` is not required by OmniDoer and is not used by default.

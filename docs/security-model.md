# Security Model

The model is not a security boundary.

Security boundaries:

- Codex CLI remains the only model/agent inference entry.
- OmniDoer tools run as local MCP/sidecar actions on the user's own runtime.
- Codex/GPT remains the sole inference engine; the security boundary never runs
  inside model output paths.
- Secret Broker validates origin and policy before credential use.
- Vault encrypts secret payloads with Argon2id-derived keys and AES-GCM.
- Session and request identifiers are bound to device, timestamp, nonce, request id,
  and origin for every sensitive control interaction.
- Control Client sends secrets and challenge responses through the secure channel.
- Challenge Relay never returns answers.
- Human Takeover never returns user input.
- Frame metadata (frame id, delivered viewport, capture timestamp) is required
  before takeover input is accepted by the browser worker.
- Audit log is hash-chained and redacted.
- Error and exception fields are treated as sensitive surfaces because browser,
  challenge, or takeover failures may otherwise echo user input.

Challenge-stream contract:

- Browser screenshots and DOM snapshots are redacted before any model-visible
  observation reaches Codex.
- For CAPTCHA, anti-bot pages, passkey/WebAuthn prompts, registration captchas,
  and 3DS challenges, OmniDoer pauses the agent and streams the live control
  surface to the paired client.
- The user inputs in the takeover path through the same authenticated Cloud Direct
  session; no challenge solution or secret enters the model context.
- The browser must be in a current `frame_id`/viewport/window-hints state when the
  request is resumed.
- The agent only resumes after explicit release from the Control Client when the
  user has completed the interaction and policy revalidation succeeds.
- Every resume action rechecks scope and origin; stale or mismatched takeover state
  is rejected.

Reproducible safety guarantees:

- All challenge payloads are redacted at transport entry and at browser observation
  boundaries.
- No challenge answer, verification code, or passkey material is ever stored.
- Approval requests for high-risk actions include review fingerprints (merchant,
  amount, currency, origin, final action marker, intent) and are consumed after
  one successful replay-resistant release.

Operational rule:

- The Agent can request action.
- The Broker and policy layer decide whether the request is scoped and allowed.
- The Vault releases only credential use, not credential value.
- Human challenge, registration, passkey, and anti-bot interactions stay in the
  Control Client takeover path.
- Final payments, OAuth grants, account changes, uploads, and message sends
  require scoped human approval that is consumed before release.

`OPENAI_API_KEY` is not required by OmniDoer and is not used by default.

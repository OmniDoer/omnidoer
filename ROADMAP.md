# Roadmap

## Milestone 0: GitHub Bootstrap

- Fork `openai/codex` to `omnidoer/omnidoer`.
- Create `omnidoer-mvp`.
- Add initial OmniDoer docs, demo site, redaction tests, and policy tests.

## Milestone 1: Repository Structure and Docs

- Finalize the sidecar structure.
- Add CI for formatting, tests, secret scanning, and redaction regression tests.
- Document MCP tools, broker behavior, browser redaction, approval, and threat model.

## Milestone 2: Browser Controller

- Open URL, click, type, select, upload, download, observe DOM, observe accessibility tree, capture guarded screenshots, and report current origin.
- Route every observation through the redactor.

## Milestone 3: Vault and Broker

- Implement encrypted local vault.
- Implement interactive credential creation with secure prompts.
- Fill the local demo login through the broker.
- Prove secrets do not appear in model-visible outputs, logs, audits, DOM observations, accessibility observations, or exceptions.

## Milestone 4: MCP Tools

- Implement `omni-mcp`.
- Expose only safe action tools.
- Add schema and forbidden-tool tests.

## Milestone 5: Approval and Mock Payment

- Implement mock checkout.
- Block final submit until approval.
- Verify deny prevents submission and approve allows only the local mock payment.

## Milestone 6: Codex Integration

- Let Codex CLI call OmniDoer MCP tools.
- Complete the demo task: log in to the local site and download an invoice.

## Milestone 7: Telegram Bridge

- Add low-sensitivity notifications and approvals.
- Keep Telegram disabled by default.
- Do not accept plaintext passwords through Bot API.

## Milestone 8: Security Hardening

- Add origin exact-match, punycode/homograph, iframe, form-action, HTTP, prompt-injection, redaction, payment-policy, and audit-integrity tests.

## Current Progress Snapshot

- Cloud Direct is the primary deployment model. The root Pages site and project
  Pages site both publish one-command install instructions for local and Cloud
  Direct setups.
- Control Client pairing uses device identity, signed requests, CSRF, origin
  checks, rate limiting, and request/device scoping.
- Secret and challenge submissions are encrypted to the broker path and are not
  returned through MCP or model-visible outputs.
- Human Takeover and Registration Handoff stream the live browser to the
  Control Client, pause the Agent, route allowed touch/keyboard/text events
  back to the controlled browser, and release control back to the Agent.
- Takeover events are allowlisted, length-limited, audited by event category
  only, and rejected without echoing user-provided text.
- Takeover browser frames now carry `frame_id`, `captured_at`, viewport
  metadata, and `input_binding_required`; Control Client input is bound to the
  currently visible frame, and stale or mismatched frame input is rejected
  before it reaches the browser worker.
- Payment approvals include structured merchant, amount, recipient, origin,
  final-button, after-approval, and review-fingerprint details. Final sensitive
  browser clicks are gated on scoped approval.

## Immediate Next Work

- Continue improving mobile takeover ergonomics: frame freshness indicators,
  reconnect behavior, zoom/pan handling, and WebSocket/WebRTC-ready frame
  transport while preserving the same security boundary.
- Expand end-to-end tests proving that registration, CAPTCHA/passkey handoff,
  payment approval, and frame-bound takeover input never leak secrets or
  challenge answers to logs, MCP, model-visible observations, screenshots, or
  errors.
- Keep README, Pages, release notes, and this roadmap updated after each
  substantial change so the project can be resumed from repository state alone.

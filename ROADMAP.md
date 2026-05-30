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

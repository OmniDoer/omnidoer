# Threat Model

## Assets

- Vault passphrases and derived encryption keys.
- Login credentials, TOTP seeds, recovery codes, cookies, API keys, payment data, private keys, OAuth codes, and session identifiers.
- User intent and approval decisions.
- Browser profiles, downloads, audit logs, and policy files.

## Adversaries

- Prompt injection content inside web pages.
- Malicious iframes, form-action rewrites, lookalike domains, and HTTP downgrades.
- Compromised or over-broad MCP tools.
- Accidental logging, panic output, debug traces, screenshots, DOM snapshots, or accessibility dumps.
- A model that can reason about tool outputs but is not trusted with secrets.
- Local malware is out of scope for early MVP, but the design should not make local compromise worse by exporting plaintext secrets.

## Trust Boundaries

- The model is untrusted for secret handling.
- Browser-observed page content is untrusted.
- The Secret Broker owns credential-use decisions.
- The vault owns encryption, unlock, and plaintext lifetime.
- The browser controller owns current URL, origin, frame tree, field metadata, form action, and injection primitives.
- The redactor is the only path from browser observations to model-visible text or images.
- The approval layer owns final sensitive-action submission.

## Primary Risks

- A prompt injection asks the model to reveal, copy, or exfiltrate credentials.
- A page looks like the allowed origin but posts credentials to a different action URL.
- A login form is embedded in a malicious iframe.
- A password reveal button changes a masked field into model-visible text.
- A screenshot or accessibility tree leaks a fake secret during debugging.
- A payment button is clicked before the user approves the final details.

## Required Mitigations

- Exact origin checks before credential fill.
- HTTPS by default, with loopback HTTP allowed only for local demos.
- Top-level frame checks before login fill.
- Form-action origin checks before credential fill.
- Redaction of secret-like text in DOM, accessibility, network summaries, and logs.
- Screenshot blocking or masking when sensitive controls are visible.
- Hash-chained audit logs without secrets.
- Human approval before payments, purchases, transfers, subscriptions, OAuth grants, account deletion, password changes, 2FA changes, and sensitive message sending.

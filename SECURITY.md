# Security Policy

OmniDoer is designed around one rule: the agent may request use of a secret,
but the agent must never read the secret itself.

## Non-Negotiable Boundaries

- Model context must never contain passwords, TOTP seeds, cookies, payment credentials, private keys, API keys, recovery codes, or decrypted vault records.
- MCP tool results must never contain secrets.
- Terminal output, logs, audit events, panic messages, and debug traces must never contain secrets.
- DOM snapshots and accessibility trees must not include password field values.
- Screenshots must not expose password, card, TOTP, recovery-code, or token regions.
- Default credential fill is exact-origin only.
- HTTP, iframe fill, form-action mismatch, suspicious homograph domains, payment submission, OAuth grants, password changes, account deletion, and 2FA changes are blocked or require explicit approval.

## Forbidden Interfaces

Do not add tools, commands, debug endpoints, or helper APIs that return secrets,
including equivalents of:

- `get_password`
- `decrypt_password`
- `get_totp_code`
- `get_cookie`
- `get_api_key`
- `export_secret`
- `print_secret`
- `copy_secret_to_clipboard`
- `dump_cookies`
- `dump_local_storage`
- `dump_password_values`
- `read_private_key`
- `export_private_key`

Allowed interfaces must be action-oriented, for example:

- `credential.fill_current_origin_login()`
- `credential.fill_current_origin_totp()`
- `credential.open_authenticated_session()`
- `credential.use_api_key_for_allowed_request()`
- `credential.sign_with_key_without_exporting()`
- `payment.prepare_review()`
- `payment.request_user_approval()`

## Reporting Security Issues

Until this project has a dedicated private disclosure channel, do not publish
working exploit details in public issues. Open a minimal public issue that says
a private security report is needed, without credentials, tokens, logs, or
proof-of-concept payloads.

## Development Rules

- Use fake local demo credentials only.
- Do not automate real financial, exchange, ticketing, government, or production account flows in tests.
- Do not bypass CAPTCHA, rate limits, MFA, paywalls, fraud controls, access controls, or bot detection.
- Add regression tests for every redaction or policy bypass fixed.
- Treat debug mode as production mode for secret handling.

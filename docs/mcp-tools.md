# MCP Tools

OmniDoer MCP tools expose actions, not secrets.

## Allowed Tools

- `browser.open(url)`
- `browser.observe()`
- `browser.observe_accessibility()`
- `browser.click(selector_or_description)`
- `browser.type_text(selector_or_description, text)`
- `browser.select(selector_or_description, value)`
- `browser.upload_file(selector_or_description, path)`
- `browser.download_current_file()`
- `browser.current_origin()`
- `credential.list_for_current_origin()`
- `credential.create_interactive()`
- `credential.fill_current_origin_login(credential_id)`
- `credential.fill_current_origin_totp(credential_id)`
- `registration.request_user_handoff(origin, reason)`
- `takeover.request_user_control(origin, reason)`
- `approval.request(action_summary, risk_level, structured_details)`
- `payment.prepare_review()`
- `payment.request_user_approval()`
- `audit.show_recent_events()`
- `policy.explain_current_block()`

## Forbidden Tool Families

No MCP tool may return a password, TOTP code, cookie, local storage, session
storage, API key, private key, payment credential, recovery code, or decrypted
vault record. Tool names that imply secret export are blocked by tests.

## Result Contract

Credential tools return status and policy metadata only:

```json
{
  "status": "filled",
  "origin": "https://example.com",
  "credential_id": "cred_123",
  "fields_filled": ["username", "password"],
  "secret_returned": false
}
```

The actual username/password values are not present.

`browser.type_text` and `browser.select` are ordinary form tools. If the target
field appears to be a password, OTP, token, recovery code, payment, or other
sensitive field, the browser controller rejects the call and requires the
Secret Broker or Challenge Relay path instead.

`browser.observe_accessibility` returns a redacted accessibility snapshot for
model-visible reasoning. It must not include password values, verification
codes, payment details, or challenge answers.

`browser.upload_file` sends a local file path to the controlled browser file
input without returning file contents. If the caller marks the upload as
`sensitive: true`, OmniDoer creates a `file_upload` approval request and
requires that request to be approved before the upload is allowed.

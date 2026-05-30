# Secret Broker

The Secret Broker is the only component allowed to cause a secret to be used.
It must not expose the secret to Codex, MCP clients, logs, audit output, or
debug output.

## Transport

- Use a Unix domain socket by default.
- Do not open a TCP listener by default.
- Authenticate local clients before accepting broker commands.
- Keep plaintext secret lifetime short and inside the broker-controlled path.

## Credential Fill Flow

1. MCP receives `credential.fill_current_origin_login(credential_id)`.
2. Broker asks the browser controller for current URL, top-level origin, frame tree, target fields, and form action.
3. Broker loads only credential metadata first.
4. Policy checks exact origin, HTTPS or loopback demo HTTP, top-level frame, form-action origin, suspicious punycode/homograph domains, and credential `allowed_origins`.
5. Vault decrypts only after policy allows the action.
6. Browser receives the username/password through a non-observed injection path.
7. Broker returns status, field count, origin, policy decision, and audit event ID.

## Forbidden Broker Behavior

- Returning decrypted passwords.
- Returning TOTP codes or seeds.
- Returning cookies, local storage, session storage, private keys, or API keys.
- Copying secrets to clipboard by default.
- Logging form values.
- Trusting the model's claim about the current page.

## Early MVP Notes

Loopback HTTP can be allowed for the local demo only. Non-loopback HTTP should
be blocked for credential fill.
Punycode domains and mixed-script homograph-looking domains are blocked for
credential fill until a future policy layer can require stronger manual review.

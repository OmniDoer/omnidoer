# Browser Redaction

Every browser observation that can reach the model must pass through the
observer redactor first.

## Redacted Surfaces

- DOM text.
- DOM attributes and input values.
- Accessibility tree names, values, and descriptions.
- Network event summaries.
- Console output.
- Error messages.
- Screenshots or screenshot metadata.

## Required Redactions

- Password fields: never include the value.
- TOTP, OTP, MFA, recovery code, and backup code fields.
- Cookies and session identifiers.
- API keys and bearer tokens.
- OAuth authorization codes.
- Private keys and seed phrases.
- Card numbers, bank account numbers, and payment credentials.

## Password Reveal Rule

If a page turns a password field into visible text or provides a "show
password" control, OmniDoer must stop screenshotting and must not observe that
region until it is masked or excluded.

## Early Implementation

The initial Python redactor is a safety fixture for tests. The production
observer may be Rust or TypeScript, but it must preserve the same non-leakage
properties.

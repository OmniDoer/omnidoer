# Challenge Relay

Challenge Relay handles MFA, one-time codes, CAPTCHA acknowledgements, passkey
instructions, WebAuthn instructions, 3DS, and device confirmations.

It returns status only:

```json
{
  "status": "challenge_completed",
  "completed_by_user": true,
  "bypassed": false,
  "secret_exposed_to_model": false
}
```

It must not return challenge answers, verification codes, CAPTCHA content, or
passkey material.

The Agent resumes only after the Control Client supplies an encrypted response
or the user explicitly completes the handoff. If a challenge request expires or
is rejected, the wait exits with a sanitized failure status instead of waiting
until a generic timeout or logging the user-provided value.

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

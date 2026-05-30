# Telegram

Telegram is an optional notification bridge and is disabled by default.

Telegram Bot API is not Telegram Secret Chat. Bot messages must not be treated
as an end-to-end encrypted secret input channel.

Allowed:

- Notify that a request is pending.
- Tell the user to open OmniDoer Control Client.
- Low-sensitivity status updates.

Not allowed:

- Plaintext passwords.
- TOTP seeds.
- SMS or email codes.
- CAPTCHA answers.
- Private keys.
- Payment credentials.
- Human Takeover streaming.

High-sensitivity interaction belongs in the Control Client.

The runtime bridge is notify-only. Its payloads may contain request metadata
such as `request_id`, request type, origin, risk level, and a Control Client
URL. They must not contain secret fields, challenge answers, browser frames,
session tokens, pairing tokens, or takeover user input.

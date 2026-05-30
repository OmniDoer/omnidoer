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

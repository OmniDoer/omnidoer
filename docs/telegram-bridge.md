# Telegram Bridge

The Telegram bridge is experimental and disabled by default.

## Allowed Uses

- Low-sensitivity task notifications.
- Approval prompts for already-redacted structured details.
- Status updates such as task started, blocked, approved, denied, or completed.

## Disallowed Uses

- Receiving plaintext passwords through Telegram Bot API.
- Receiving TOTP seeds, recovery codes, API keys, payment credentials, or private keys.
- Treating a Telegram Bot private chat as end-to-end encrypted secret input.

## Bot API vs Secret Chat

Telegram Bot API chats are not the same as Telegram Secret Chats. Bot messages
are processed through Telegram's bot infrastructure and must not be treated as
an end-to-end encrypted password channel. If OmniDoer ever supports remote
secret entry over Telegram, it must implement its own client-side E2EE where
the bot relays ciphertext only.

# Slash commands

For an overview of Codex CLI slash commands, see [this documentation](https://developers.openai.com/codex/cli/slash-commands).

OmniDoer adds `/pair` in the native console. It submits a short instruction to
the Agent to call `control.create_pairing`, returning a one-time Control Client
pairing URL. Use optional inline text for pairing options, for example:

```text
/pair https://agent.example.com 30m
```

Pairing is a setup step, not a per-request requirement. After the Control
Client pairs successfully, the device uses its cached, revocable session for
ordinary credential entry, approval, challenge, and takeover requests.

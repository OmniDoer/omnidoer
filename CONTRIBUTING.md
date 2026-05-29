# Contributing

OmniDoer accepts changes that improve local-first web action capability without
weakening secret handling.

## Development Principles

- Keep upstream Codex CLI mergeable.
- Prefer sidecars, MCP tools, plugins, and small integration hooks.
- Never add tools that return secrets.
- Add tests for redaction, policy decisions, audit behavior, and approval gates.
- Use the local demo site before attempting any real website automation.

## Local Checks

For current OmniDoer sidecar files:

```sh
python3 -m unittest discover -s tests
python3 omnidoer/scripts/secret_scan.py
```

For Rust or upstream Codex changes, follow the existing `AGENTS.md` guidance
for the touched crate.

## Scope Boundaries

Pull requests must not implement CAPTCHA bypass, fraud-control bypass, MFA
bypass, credential dumping, cookie dumping, fake account registration,
credential stuffing, spam sending, ticket scalping, review manipulation,
market manipulation, unauthorized purchases, or paywall bypass.

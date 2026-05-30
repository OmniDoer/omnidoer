# Control Client Release

OmniDoer Control Client is a static HTML5/PWA client served by the user's own
OmniDoer Control Service. It is not an LLM chat client and it does not call
OpenAI APIs directly.

## Release Artifact

The GitHub Release asset is:

- `omnidoer-control-client-pwa.zip`

It contains only:

- `index.html`
- `app.js`
- `style.css`
- `manifest.json`
- PWA icons

It must not contain:

- Codex auth data
- vault files
- pairing tokens
- session tokens
- passwords
- TOTP seeds
- one-time codes
- CAPTCHA or MFA answers
- payment credentials
- takeover user input

## English

Use the released PWA bundle when you want to inspect or host the Control
Client static files separately from the Python package. In normal operation,
`omnidoer control serve` serves the same UI from the local package.

## 中文

如果需要单独检查或托管 Control Client 静态文件，可以使用 GitHub Release 中的
PWA 压缩包。正常使用时，`omnidoer control serve` 会直接从 Python 包内提供同一套
界面。

## Publishing Checklist

1. Run the Python tests and Control Client JavaScript syntax check.
2. Package `omnidoer/omni_control/static/`.
3. Upload `omnidoer-control-client-pwa.zip` to the current GitHub Release.
4. Verify that the archive contains no runtime state or secret material.

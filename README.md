# OmniDoer

The agent that does.

![OmniDoer brand mark](./icon.png)

OmniDoer is the execution layer for web agents that need to do more than chat.
Codex is the brain. OmniDoer is the hands, browser, vault, broker, approval
gate, Control Client, and human-takeover bridge.

If a human can operate a website with authorization, OmniDoer is designed to
help execute that workflow safely: sign up, log in, navigate, fill forms,
download files, organize information, prepare purchases, request approvals,
and hand the live browser back to the user when a challenge or judgment call
requires a human.

![OmniDoer English edition cinematic poster](./docs/assets/localized/omnidoer-readme-en.jpg)

Localized README editions:
[中文](./README.zh-CN.md) |
[Español](./README.es.md) |
[Français](./README.fr.md) |
[Deutsch](./README.de.md) |
[日本語](./README.ja.md) |
[한국어](./README.ko.md)

The agent may request an action.
The broker checks the origin.
The vault uses the secret.
The browser receives the credential.
The model never does.

Compared with Codex alone, OmniDoer adds a real controlled browser, Secret
Broker, encrypted Vault, Challenge Relay, Human Takeover, Cloud Direct Control
Service, Approval Gate, and tamper-evident audit trail. Compared with
browser-only automation demos, OmniDoer treats secrets, CAPTCHA/MFA/passkey
handoff, payments, registration, remote control, and logs as first-class
security boundaries.

Sensitive actions such as payments, purchases, account changes, OAuth grants, and message sending require explicit human approval.

OmniDoer is not a credential stealer.
OmniDoer is not a CAPTCHA bypasser.
OmniDoer is not a fraud tool.
OmniDoer is not an autonomous spender.
OmniDoer is a user-authorized local execution layer.

智能体可以行动，但秘密必须留在本地。

OmniDoer does not call OpenAI APIs directly. It extends Codex CLI through MCP
and preserves your Codex authentication mode. If Codex is logged in with
ChatGPT, OmniDoer uses that Codex path through Codex CLI. If Codex is using an
API key, `omnidoer doctor` warns that this is OpenAI Platform API billing, but
OmniDoer does not switch modes or create a new API client.

![OmniDoer cloud-native human-in-the-loop web agent](./docs/assets/omnidoer-human-loop-web-agent.jpg)

![OmniDoer secure cloud control service](./docs/assets/omnidoer-cloud-control-service.jpg)

## Languages / 多语言

**English.** OmniDoer is a Codex CLI sidecar, MCP tool server, secure browser
runtime, Secret Broker, Control Client, Challenge Relay, Human Takeover, Cloud
Direct service, and approval layer. Codex remains the only model entrypoint;
OmniDoer turns reasoning into real user-authorized web action without
revealing secrets or challenge answers to the model.

**中文。** OmniDoer 是 Codex CLI 的 sidecar / MCP 扩展层，不是新的 OpenAI
API 客户端。它通过 Secret Broker、Vault、Control Client、Challenge Relay、
Human Takeover、Cloud Direct、Approval Gate 和审计日志，让 Codex 的推理
变成真实可控的网页行动；密码、验证码、Cookie、私钥和支付凭据不会进入模型上下文。

**Español.** OmniDoer amplía Codex CLI con herramientas MCP para acciones web
seguras. Las credenciales se usan por medio del broker local y las acciones
sensibles requieren aprobación humana.

**Français.** OmniDoer ajoute à Codex CLI une couche MCP/sidecar pour agir sur
le web avec un navigateur contrôlé, un coffre local, un broker de secrets et
des approbations humaines.

**Deutsch.** OmniDoer erweitert Codex CLI um eine sichere MCP/Sidecar-Laufzeit.
Anmeldedaten, Codes und Zahlungsfreigaben bleiben im Broker, Vault und Control
Client, nicht im Modellkontext.

**日本語.** OmniDoer は Codex CLI を MCP/sidecar として拡張するローカル優先
の実行基盤です。モデルは秘密を読み取らず、認証情報やチャレンジ処理は Control
Client と Broker の安全境界内で扱われます。

**한국어.** OmniDoer는 Codex CLI를 MCP/sidecar 방식으로 확장하는 실행 계층입니다.
비밀번호, 인증 코드, 결제 승인 정보는 모델이 아니라 Broker, Vault, Control
Client 안에서만 처리됩니다.

## Status

OmniDoer is starting as a minimal, upstream-friendly fork of OpenAI Codex CLI.
The first implementation path is a sidecar runtime, MCP tool layer, browser
controller, local vault, policy engine, approval layer, and audit log that
Codex can call without receiving secrets.

This branch is intentionally early, but the target is not a toy browser script.
The local demo site and redaction/policy tests are the proving ground for an
omni-capable runtime: real browser control, registration handoff, credential
fill, file download, challenge handoff, payment review, remote takeover, and
audit verification without leaking secrets.

## Core Rule

The model is not the security boundary.

The security boundary is the combination of:

- Secret Broker
- local encrypted vault
- browser isolation
- origin and form-action policy checks
- redacted observation layer
- human approval for sensitive actions
- audit logs that never contain secrets

The agent can ask to use a credential. It cannot read the credential.

![OmniDoer feature matrix](./docs/assets/omnidoer-feature-matrix.jpg)

## System Blueprints

These diagrams define the product direction for the Linux-based all-purpose
web action runtime: secure credential storage and login, human takeover for
2FA/anti-bot/registration, and Cloud Direct deployment on a user-owned server.

![OmniDoer secure credential lifecycle](./docs/assets/omnidoer-secure-credential-flow.svg)

![OmniDoer human takeover state machine](./docs/assets/omnidoer-human-takeover-state-machine.svg)

![OmniDoer Linux Cloud Direct runtime](./docs/assets/omnidoer-linux-cloud-runtime.svg)

## Repository Layout

- `codex-rs/`, `codex-cli/`: upstream Codex CLI code kept mergeable.
- `omnidoer/`: OmniDoer sidecar runtime and local demo code.
- `docs/`: OmniDoer design notes for broker, redaction, MCP, payments, and bootstrap.
- `tests/`: initial redaction, policy, and forbidden-tool tests.

## Local Demo

Start the mock website:

```sh
python3 -m omnidoer.demo.server --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/`.

The demo includes login, TOTP, dashboard, invoice download, checkout, malicious
prompt injection, malicious iframe, form-action mismatch, HTTP downgrade,
password reveal, fake token leak, fake card number, OAuth grant, and account
deletion pages. It uses only fake local data.

## Codex Integration

Add OmniDoer to Codex as an MCP sidecar:

```sh
codex mcp add omnidoer -- omnidoer mcp serve
```

Control Client and demo agent commands do not require `OPENAI_API_KEY`.

```sh
omnidoer doctor
omnidoer control serve --host 127.0.0.1 --port 8787
omnidoer control submit-task "登录 demo 网站并下载我的发票"
omnidoer mcp serve --self-test
```

The Control Client task panel writes to a local queue. Codex can read queued
tasks with `control.next_user_task` over MCP while keeping Codex CLI as the
only model inference entrypoint.

## Control Client

OmniDoer Control Client is the unified user surface for tasks, credential
requests, one-time codes, CAPTCHA/MFA/Passkey/WebAuthn/3DS handoff, Human
Takeover, payment approvals, vault metadata, and audit summaries.

Registration Handoff handles the case where the target website requires a new
user account. The Agent can open the registration page, then pause and proxy
that live browser session to the Control Client. The user completes signup,
verification, CAPTCHA/passkey prompts, and terms acceptance directly. OmniDoer
does not automate fake or bulk registration, and registration secrets or
challenge answers are not returned to Codex/MCP.

Local development can run on `127.0.0.1`. Cloud Direct Mode lets Android,
Windows 11, and PWA clients connect directly to the user's own cloud server
over HTTPS/WSS with pairing, device identity, session auth, origin protection,
rate limiting, and end-to-end encrypted secret submission.

```sh
omnidoer control serve --cloud-direct \
  --host 0.0.0.0 \
  --port 8787 \
  --public-url https://agent.example.com \
  --behind-reverse-proxy

omnidoer control pair --print-qr
```

MCP remains local to Codex CLI. Vault, Broker, Challenge Relay, and browser
internal interfaces are not public Control Service APIs.

![OmniDoer Cloud Direct architecture](./docs/assets/omnidoer-cloud-direct.svg)

## Client Release

The PWA Control Client is packaged from `omnidoer/omni_control/static/` and
published as a GitHub Release asset named `omnidoer-control-client-pwa.zip`.
The release artifact is static UI only; it does not contain model credentials,
Codex auth data, vault data, pairing tokens, session tokens, secrets, or
challenge answers.

## MVP Target

The first accepted end-to-end flow is:

```sh
omnidoer init
omnidoer vault create
omnidoer cred add --origin http://localhost:PORT
omnidoer demo start
omnidoer agent run "登录 demo 网站并下载我的发票"
```

Expected safety properties:

- The broker verifies the current origin before filling credentials.
- The browser receives credentials through a broker-controlled path.
- MCP tool results never contain passwords, TOTP seeds, cookies, API keys, or private keys.
- DOM and accessibility observations redact password fields and secret-like values.
- Audit logs record actions and policy decisions without secrets.
- Mock payment submission stops for human approval.

## Upstream

OmniDoer is forked from [openai/codex](https://github.com/openai/codex).
Changes should remain small and mergeable with upstream. Prefer adding
OmniDoer functionality as a sidecar, plugin, MCP server, or narrowly scoped
integration layer before modifying Codex core crates.

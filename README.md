# OmniDoer

The agent that does.

![OmniDoer brand mark](./icon.png)

OmniDoer is the execution layer for agents that need to operate the web, not
just talk about it. Its product thesis is simple: if an authorized human can
complete a workflow in a browser, OmniDoer should be able to help complete that
workflow inside a strict security boundary.

Codex remains the reasoning engine. OmniDoer adds the controlled browser,
Linux-side runtime, Secret Broker, encrypted Vault, Control Client, challenge
relay, approval gate, audit trail, and human-takeover bridge that turn model
reasoning into user-authorized web action.

The target is broad web capability without unsafe shortcuts: sign up, log in,
navigate, fill forms, download files, organize information, prepare purchases,
review payments, and hand the live browser to the user whenever a site requires
human authentication, judgment, or consent.

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

OmniDoer is designed to give cloud-model agents more operational freedom than
chat-only or browser-only tools while preserving the user's security boundary.
The model can plan and ask; the Broker, Vault, policy engine, browser
isolation, approval gate, and Control Client decide what may actually happen.

The Control Client connects to the user's own Linux server over Cloud Direct
Mode. When a page requires CAPTCHA, graphical verification, MFA, passkey,
WebAuthn, 3DS, registration confirmation, or an anti-bot interaction,
OmniDoer does not bypass the mechanism. It pauses the Agent, projects the live
browser session to the user's client, accepts user input through the takeover
channel, then resumes the Agent after Release Control.

Payments, purchases, account changes, OAuth grants, message sending, and other
sensitive actions stop at an approval gate. The Agent can prepare the action;
the user decides whether it proceeds.

Compared with Codex alone, OmniDoer adds a real controlled browser, Secret
Broker, encrypted Vault, Challenge Relay, Human Takeover, Cloud Direct Control
Service, Approval Gate, and tamper-evident audit trail. Compared with local
browser automation demos, OmniDoer treats credential storage, CAPTCHA/MFA/
passkey handoff, payment approval, registration, remote control, and logs as
first-class security boundaries.

The result is a cloud-Codex architecture for high-freedom web action: it can
inherit Codex/GPT model capability, multimodal reasoning, and existing Codex
authentication or billing paths, while keeping passwords, OTP seeds, cookies,
private keys, payment credentials, challenge answers, and takeover inputs out
of model-visible context.

OmniDoer is not a credential stealer.
OmniDoer is not a CAPTCHA bypasser.
OmniDoer is not a fraud tool.
OmniDoer is not an autonomous spender.
OmniDoer is a user-authorized local execution layer.

The agent may act. Secrets stay inside the controlled security boundary.

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

OmniDoer is an upstream-friendly fork of OpenAI Codex CLI with a separate
sidecar runtime for web action. The fork keeps Codex auth, model selection, and
billing behavior intact while adding the execution system Codex needs in order
to operate websites safely.

The project is still early, but the target is intentionally ambitious: an
omni-capable web runtime with real browser control, secure credential storage,
automatic login, 2FA and anti-bot handoff, registration handoff, file download,
payment review, remote takeover, audit verification, and redaction tests that
prove secrets do not enter model-visible outputs.

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

The guarded browser flow extends that target:

```sh
omnidoer agent run "guarded browser 2FA 智能切换"
```

It logs in with a Vault credential, detects the TOTP page, routes it through
Challenge Relay, resumes at the dashboard, opens the anti-bot mock page, hands
control to the user, then resumes the Agent after Release Control.

Expected safety properties:

- The broker verifies the current origin before filling credentials.
- The browser receives credentials through a broker-controlled path.
- MCP tool results never contain passwords, TOTP seeds, cookies, API keys, or private keys.
- DOM and accessibility observations redact password fields and secret-like values.
- Audit logs record actions and policy decisions without secrets.
- Mock payment submission stops for human approval.
- 2FA and anti-bot pages trigger user completion instead of automated bypass.
- Human takeover frames are for the Control Client only and are not sent to the model.

## Upstream

OmniDoer is forked from [openai/codex](https://github.com/openai/codex).
Changes should remain small and mergeable with upstream. Prefer adding
OmniDoer functionality as a sidecar, plugin, MCP server, or narrowly scoped
integration layer before modifying Codex core crates.

# OmniDoer

**安全可控，才能更自由。**

![OmniDoer 中文版电影质感海报](./docs/assets/localized/omnidoer-readme-zh-CN.jpg)

[English](./README.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

落地页： [https://omnidoer.github.io/](https://omnidoer.github.io/)

项目页默认会带上仓库路径；如果你要纯根域 `omnidoer.github.io`，可以使用
`omnidoer.github.io` 用户站仓库（推荐）或将该 Pages 绑定到自定义域。

OmniDoer 目标是把“人类能在网页上完成的动作”安全地交给智能体延续执行：如果用户有权限在网页上完成一个流程，OmniDoer 在不越界的前提下可把该流程接上去。
关键规则是：模型负责推理与决策，执行在用户自己控制的 Linux 服务器里完成，任何密钥、验证码、支付决策都不允许离开安全边界。

## 一键部署

本地开发安装：

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | sh
```

在自己的 HTTPS 反向代理后部署 Cloud Direct 服务器：

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | \
  OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com sh
```

安装后生成配对码并提交任务：

```sh
~/omnidoer/.venv/bin/omnidoer control pair --print-qr
~/omnidoer/.venv/bin/omnidoer control submit-task "打开本地 demo 并下载我的发票"
```

后续一键升级 CLI 与 sidecar：

```sh
~/omnidoer/.venv/bin/omnidoer upgrade
~/omnidoer/.venv/bin/omnidoer --version
```

安装脚本会创建 `~/omnidoer/.venv`、初始化 OmniDoer、安装浏览器 worker、
自检 MCP server，并在 `codex` CLI 可用时注册 `omnidoer mcp serve`。它会
保留现有 Codex 登录、模型选择和计费路径，不把 OmniDoer 变成新的默认 OpenAI
API 客户端。

OmniDoer 是 Codex CLI 的 MCP/sidecar 全能网页行动层，不是新的 OpenAI API 客户端。Codex 负责推理，OmniDoer 负责真实执行：打开网页、注册账号、登录、填写表单、下载文件、整理资料、准备订单、请求审批，并在挑战或高风险页面前把控制权交还给用户。

如果一件事需要人类授权后在网页上完成，OmniDoer 的目标就是在安全边界内接力完成。它补上原版 Codex 缺少的真实浏览器、Secret Broker、Vault、Control Client、Challenge Relay、Human Takeover、Cloud Direct、Approval Gate、错误脱敏和审计链。

### 为什么超越 OpenClaw/Codex 自动化边界

OpenClaw 一类的浏览器自动化擅长低风险点按流程，但在验证码、反爬、passkey、3DS
和支付确认时通常无从安全衔接；纯 Prompt 的 Codex 又缺少可控执行面。OmniDoer
把推理与执行分层，把 Codex 保持在决策平面，执行平面运行在用户自己的 Linux
服务器：

- **安全边界不下沉到模型**：模型负责计划与判断，密码、TOTP 种子、cookie、支付
  信息都留在 Secret Broker、Vault、浏览器控制器和 Control Client。
- **按场景自动切换人机协同**：反爬、验证码、注册、passkey、3DS、OAuth 授权和
  支付确认由用户在客户端完成，模型仅接着返回的脱敏状态继续推进。
- **更低成本与更高自由度**：沿用现有 Codex 登录与账单模型，不新增默认 API
  收费路径，保留 Codex 的多模态上下文能力。
- **更少“越界”失败**：OmniDoer 不破解 anti-bot，也不替人完成同意/支付，而是
  自动将关键阶段挂起并切回用户客户端，完成后再恢复自动执行。

核心规则：Agent 可以请求使用 secret，但不能读取 secret。Codex 仍然是唯一模型推理入口，OmniDoer 不默认要求 `OPENAI_API_KEY`，不创建新的 OpenAI API billing path，也不修改 Codex 的 ChatGPT 登录、计费或模型提供方逻辑。

Control Client 负责凭据输入、挑战交互、Human Takeover、注册代理、支付审批和审计查看。遇到 CAPTCHA、MFA、Passkey、WebAuthn、3DS、账号注册确认或高强度 anti-bot 页面时，OmniDoer 不绕过、不破解、不代答，而是把真实浏览器页面或挑战请求交给用户本人完成。

Cloud Direct Mode 允许 Android、Windows 11 和 PWA 客户端直接连接用户自己的云服务器。公网模式必须显式启用 HTTPS/WSS、pairing、设备身份、会话认证、Origin/CSRF 防护、限速和端到端加密 secret submission。

安全测试覆盖：

- `tests/test_broker_origin.py`、`tests/test_policy.py`、`tests/test_ci_contract.py`：来源策略与合约校验。
- `tests/test_vault.py`、`tests/test_challenge_guard.py`、`tests/test_challenge_relay.py`：凭据加密、挑战拦截、流转路径。
- `tests/test_control_auth.py`、`tests/test_control_csrf_origin.py`、`tests/test_control_rate_limit.py`：设备配对、签名会话、CSRF、反滥用边界。
- `tests/test_redactor.py`、`tests/test_audit.py`：脱敏与审计可靠性。
- `tests/test_takeover_stream.py`：人机接管帧、控制权恢复链路。

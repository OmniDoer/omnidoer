# OmniDoer

**安全可控，才能更自由。**

![OmniDoer 白帽安全边界主视觉](./docs/assets/omnidoer-whitehat-hero.jpg)

[English](./README.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

落地页： [https://omnidoer.github.io/](https://omnidoer.github.io/)

一名白帽安全研究员发现了云端编码智能体里最危险的空洞：当 Agent 直接在服务器上执行时，密码、SSH 私钥、API token、应用密钥，甚至加密货币钱包密钥，都可能离模型只有一次工具调用的距离。要求模型“不要读取这些信息”，本质上只是请求模型自觉，不是真正的隔离。

OmniDoer 把这个发现转化为产品架构。Codex 保留为推理大脑，继续使用原有登录、模型选择和额度路径；OmniDoer 提供受控的执行双手：真实浏览器、Secret Broker、加密 Vault、审批门、Challenge Relay、审计链和 Control Client，把敏感动作挡在模型可见状态之外。

OmniDoer 目标是把“人类能在网页上完成的动作”安全地交给智能体延续执行：如果用户有权限在网页上完成一个流程，OmniDoer 在不越界的前提下把该流程接上去。关键规则是：模型负责推理与决策，执行在用户自己控制的 Linux 服务器里完成，任何密钥、验证码、支付决策都不允许离开安全边界。

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
~/omnidoer/.venv/bin/omnidoer
~/omnidoer/.venv/bin/omnidoer control pair --print-qr
~/omnidoer/.venv/bin/omnidoer control submit-task "打开本地 demo 并下载我的发票"
```

在 OmniDoer 原生控制台里也可以直接输入 `/pair`。这个命令会让 Agent 通过安全的
`control.create_pairing` MCP 工具生成短期 Control Client 配对链接。设备只需要
配对一次，后续正常使用会复用可撤销的设备会话，不需要每次重新配对。

不带子命令运行 `omnidoer` 会直接进入 OmniDoer 品牌交互控制台。它继承现有
Codex 的 ChatGPT 登录和计费路径，但启动器会注入 OmniDoer 品牌环境；当本机
使用支持该品牌开关的原生控制台时，启动页、`/status` 和额度展示都会明确显示
当前是在使用 OmniDoer。
如果本机已安装 `/usr/local/lib/omnidoer/codex`，`omnidoer` 会优先使用这个
OmniDoer 原生控制台；否则自动回退到保留的系统 Codex 二进制 `/usr/bin/codex`。

### 原生控制台账号切换

在原生控制台中输入 `/users` 会打开本机已登录账号切换器。列表会标记当前账号，
支持上下键选择并按 Enter 切换。OmniDoer 会把每个账号保存到独立的本地认证槽位，
在不新建对话的情况下让运行中的 app-server 原地重新加载凭据，当前上下文会继续
留在同一个会话里。需要切到具备特定能力的 ChatGPT/Codex 账号，或当前账号额度
用尽时切换到另一个账号，都可以使用这个入口。

账号选择器和日志不会打印 token、API key、私钥等凭据值；账号索引只保存展示
所需的元数据，敏感凭据仍留在配置的本地 credential store 中。

后续一键升级 CLI 与 sidecar：

```sh
~/omnidoer/.venv/bin/omnidoer upgrade
~/omnidoer/.venv/bin/omnidoer --version
```

从交互式终端启动 `omnidoer` 时，它会先检查 `origin/main` 是否存在可快进的新版本，
并询问是否立即运行 `omnidoer upgrade`。非 TTY 启动不会弹出提示；设置
`OMNIDOER_UPDATE_CHECK=0` 可关闭这个检查。

安全地让本机 `codex` 解析到 OmniDoer shim，同时保留原始 Codex CLI 在
`/usr/bin/codex`：

```sh
sudo omnidoer/scripts/install-codex-shim.sh
omnidoer/scripts/verify-codex-shim.sh
```

失败或不满意时可立即回退：

```sh
sudo omnidoer/scripts/uninstall-codex-shim.sh
sudo rm -f /usr/local/lib/omnidoer/codex
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

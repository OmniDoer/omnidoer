# OmniDoer

![OmniDoer 中文版电影质感海报](./docs/assets/localized/omnidoer-readme-zh-CN.jpg)

[English](./README.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

OmniDoer 是 Codex CLI 的 MCP/sidecar 扩展层，不是新的 OpenAI API 客户端。它让 Agent 可以打开网页、填写普通表单、下载文件、准备订单、请求审批，并把密码、验证码、TOTP、Cookie、私钥和支付凭据留在 Secret Broker、Vault 与 Control Client 的安全边界内。

核心规则：Agent 可以请求使用 secret，但不能读取 secret。Codex 仍然是唯一模型推理入口，OmniDoer 不默认要求 `OPENAI_API_KEY`，不创建新的 OpenAI API billing path，也不修改 Codex 的 ChatGPT 登录、计费或模型提供方逻辑。

Control Client 负责凭据输入、挑战交互、Human Takeover、注册代理、支付审批和审计查看。遇到 CAPTCHA、MFA、Passkey、WebAuthn、3DS 或高强度 anti-bot 页面时，OmniDoer 不绕过、不破解、不代答，而是把真实浏览器页面或挑战请求交给用户本人完成。

Cloud Direct Mode 允许 Android、Windows 11 和 PWA 客户端直接连接用户自己的云服务器。公网模式必须显式启用 HTTPS/WSS、pairing、设备身份、会话认证、Origin/CSRF 防护、限速和端到端加密 secret submission。

# OmniDoer

![OmniDoer 日本語版シネマティックポスター](./docs/assets/localized/omnidoer-readme-ja.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [한국어](./README.ko.md)

OmniDoer は Codex CLI を MCP と sidecar で拡張するローカル優先、Cloud Direct 対応の実行基盤です。新しい OpenAI API クライアントではありません。モデル推論の入口は Codex CLI のままで、Codex の認証、課金、モデル provider の仕組みを変更しません。

Agent は secret の使用を要求できますが、secret 自体を読むことはできません。パスワード、認証コード、TOTP seed、Cookie、秘密鍵、支払い情報は Secret Broker、Vault、Browser Controller、Control Client の安全境界内に残ります。

Control Client はタスク入力、認証情報入力、チャレンジ処理、Human Takeover、アカウント登録の代理、支払い承認、監査表示を統合します。CAPTCHA、MFA、Passkey、WebAuthn、3DS、強い anti-bot では、OmniDoer は回避や自動解答を行わず、ユーザー本人に操作を渡します。

Cloud Direct Mode では Android、Windows 11、PWA クライアントがユーザー自身のクラウドサーバーへ直接接続します。HTTPS/WSS、pairing、device identity、session、CSRF/Origin protection、rate limit、E2EE secret submission が必要です。

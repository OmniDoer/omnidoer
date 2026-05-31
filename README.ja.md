# OmniDoer

![OmniDoer ホワイトハット安全境界ビジュアル](./docs/assets/omnidoer-whitehat-hero.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [한국어](./README.ko.md)

**安全に制御できてこそ、より自由に任せられます。**

あるホワイトハット研究者は、クラウド型コーディングエージェントに欠けている境界を
見つけました。実サーバー上では、パスワード、SSH 鍵、API token、秘密鍵、
ウォレットシークレットが、たった一つの tool call の先にある可能性があります。
「読まないで」とモデルに頼むことは、隔離ではなく行動上のお願いにすぎません。

OmniDoer はその発見をアーキテクチャに変えます。Codex は推論の頭脳として
ログイン、モデル選択、クォータを保ち、OmniDoer は安全な手を提供します。
制御ブラウザ、Secret Broker、暗号化 Vault、承認ゲート、Challenge Relay、
監査、Control Client によって、機微な操作をモデル可視状態の外に置きます。

ページ: [https://omnidoer.github.io/omnidoer/](https://omnidoer.github.io/omnidoer/)

## クイックインストール

推奨 npm Bootstrap:

```sh
npm install -g @omnidoer/omnidoer
omnidoer
omnidoer pair
```

npm パッケージは軽量な Node ランチャーをインストールします。初回実行時に
既定では OmniDoer を `~/.omnidoer/npm-install/omnidoer` へ clone し、Python
sidecar runtime をインストールし、既存の Codex ログイン、モデル、quota、
billing 経路を保ちます。既存 checkout を使う場合は `OMNIDOER_INSTALL_DIR` を
設定します。

ソースからの直接インストール:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | sh
```

自分の HTTPS リバースプロキシ配下の Cloud Direct サーバー:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | \
  OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com sh
```

インストール後:

```sh
omnidoer
omnidoer pair
omnidoer control submit-task "ローカルデモを開いて請求書をダウンロードする"
```

直接 shell installer を使い、`omnidoer` が `PATH` にない場合は
`~/omnidoer/.venv/bin/omnidoer` で同じコマンドを実行できます。

インストーラは `~/omnidoer/.venv` を作成し、OmniDoer を初期化し、
browser worker をインストールし、MCP server を self-test し、`codex` CLI
がある場合は `omnidoer mcp serve` を登録します。

対話型ターミナルから起動すると、`omnidoer` はコンソールを開く前に
`origin/main` の fast-forward 更新を確認し、`omnidoer upgrade` を実行するか
尋ねます。TTY ではない起動では表示されず、`OMNIDOER_UPDATE_CHECK=0` で
無効化できます。

### ネイティブコンソールでのアカウント切り替え

ネイティブコンソールで `/users` を入力すると、このマシンで保存済みのログイン
アカウントを切り替えるピッカーが開きます。現在のアカウントが表示され、上下キーで
選択し Enter で切り替えられます。OmniDoer は各アカウントを個別のローカル認証
スロットに保存し、実行中の app-server にその場で再読み込みさせるため、現在の
会話コンテキストは同じセッションに残ります。特定の機能を持つ ChatGPT/Codex
アカウントへ切り替えたい場合や、あるアカウントの quota が尽きた場合に使えます。

ピッカーやログに token、API key、秘密鍵などの値は表示されません。アカウント
インデックスには表示用メタデータだけを保存し、機密情報は設定済みのローカル
credential store に残ります。

OmniDoer は Codex CLI を MCP と sidecar で拡張するローカル優先、Cloud Direct 対応の実行基盤です。新しい OpenAI API クライアントではありません。Codex が推論し、OmniDoer が実ブラウザ、Secret Broker、Vault、Control Client、Challenge Relay、Human Takeover、Cloud Direct、Approval Gate、監査で実行します。

人間が承認して Web 上で実行できる作業なら、OmniDoer はそれを安全に支援することを目指します。サインアップ、ログイン、ナビゲーション、フォーム入力、ダウンロード、請求書、購入確認、支払い承認、そしてサイトが人間の介入を求める場面でのユーザーへの操作引き渡しです。

Agent は secret の使用を要求できますが、secret 自体を読むことはできません。パスワード、認証コード、TOTP seed、Cookie、秘密鍵、支払い情報は Secret Broker、Vault、Browser Controller、Control Client の安全境界内に残ります。

Control Client はタスク入力、認証情報入力、チャレンジ処理、Human Takeover、アカウント登録の代理、支払い承認、監査表示を統合します。CAPTCHA、MFA、Passkey、WebAuthn、3DS、登録確認、強い anti-bot では、OmniDoer は回避や自動解答を行わず、ユーザー本人に操作を渡します。

Cloud Direct Mode では Android、Windows 11、PWA クライアントがユーザー自身のクラウドサーバーへ直接接続します。HTTPS/WSS、pairing、device identity、session、CSRF/Origin protection、rate limit、E2EE secret submission が必要です。

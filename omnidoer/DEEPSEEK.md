# DeepSeek V4 in `/model`

OmniDoer can show `deepseek-v4-flash` and `deepseek-v4-pro` beside GPT models in the `/model`
picker. Selecting a model on another provider saves the provider, model, and reasoning effort
together, then starts a fresh conversation so requests never leak to the previous provider.

DeepSeek exposes Chat Completions and Anthropic APIs, while current Codex speaks the OpenAI
Responses API. OmniDoer therefore uses a pinned, separately built Moon Bridge sidecar to translate
the protocol. The GPL-3.0 bridge remains a separate process and artifact; OmniDoer does not copy its
source into this repository.

The bridge installer adds this provider to `~/.codex/config.toml` if it is not already present:

```toml
[model_providers.deepseek]
name = "DeepSeek V4 via Moon Bridge"
base_url = "http://127.0.0.1:38440/v1"
wire_api = "responses"
requires_openai_auth = false
```

Install the two GitHub Actions artifacts on Linux:

```sh
omnidoer/scripts/install-native-console.sh /path/to/omnidoer-codex-linux-x64
omnidoer/scripts/install-deepseek-bridge.sh /path/to/omnidoer-moonbridge-linux-x64
```

Open **Model Providers → DeepSeek V4** in the paired Control Client, or the **Passwords** tab in
OmniDoer Lite, to initialize or replace the API key. The browser encrypts it to the local Broker
with the existing request-scoped E2EE channel. The Broker consumes the ciphertext, stores the key
in the encrypted OmniDoer Vault, clears the request ciphertext, and restarts the bridge. Only
configured/active booleans are returned to the UI; no secret is submitted to chat or model context.

The durable `/etc/omnidoer/moonbridge-deepseek.yml.template` contains no key. At service start,
OmniDoer decrypts the Vault record locally and creates a mode-`0600` configuration under
`/run/omnidoer-moonbridge/`, which disappears on reboot. Never commit the real key. After
initialization, verify `http://127.0.0.1:38440/v1/models`.

## 在 `/model` 中使用 DeepSeek V4

OmniDoer 可以在 `/model` 选择器中同时显示 GPT、`deepseek-v4-flash` 和
`deepseek-v4-pro`。当目标模型属于其他 provider 时，客户端会原子保存 provider、模型和
推理强度，然后新建会话，避免请求误发给上一个 provider。

DeepSeek 提供 Chat Completions 与 Anthropic 接口，而当前 Codex 使用 OpenAI Responses
API。因此 OmniDoer 使用固定上游提交、独立构建和运行的 Moon Bridge 旁路进程做协议转换。
该 GPL-3.0 组件作为独立进程和 Actions 产物分发，源码不复制进本仓库。

桥接安装脚本会在尚未配置时把上面的 `[model_providers.deepseek]` 写入
`~/.codex/config.toml`。请在已配对的完整 Control Client 中打开“Model Providers → DeepSeek
V4”，或在 OmniDoer Lite 的“密码”页初始化/更换 API Key。浏览器沿用请求级 E2EE 通道把
key 加密给本地 Broker；Broker 消费密文后写入加密 Vault、清除请求密文并重启桥接器。
界面只返回“已配置/运行中”等布尔状态，不把 secret 发送到聊天或模型上下文。

持久化模板 `/etc/omnidoer/moonbridge-deepseek.yml.template` 不包含 key。服务启动时，
OmniDoer 才在本地解密 Vault 记录，并在 `/run/omnidoer-moonbridge/` 生成权限为 `0600`
的临时配置；重启后该文件消失。初始化后再检查
`http://127.0.0.1:38440/v1/models`，不要把真实 key 提交到 Git。

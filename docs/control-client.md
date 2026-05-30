# Control Client

The OmniDoer Control Client is the user control plane for tasks, credential
entry, challenge handling, approval, audit review, and Human Takeover Mode.

MVP commands:

```sh
omnidoer control serve --host 127.0.0.1 --port 8787
omnidoer control submit-task "登录 demo 网站并下载我的发票"
omnidoer control tasks
omnidoer control requests
omnidoer control input-secret <request_id>
omnidoer control challenge <request_id>
omnidoer control approve <request_id>
omnidoer control deny <request_id>
omnidoer control release <request_id>
```

The Chat / Task panel is a local task queue, not a new LLM chat client. The
Control Client writes user tasks to `.omnidoer/control_tasks.json`. Codex reads
them through the safe MCP tool `control.next_user_task`, then continues using
the existing Codex CLI authentication and billing mode.

In Cloud Direct Mode the same PWA connects directly to the user's own cloud
server. A pairing URL from `omnidoer control pair --print-qr` opens the Pair
Device panel, registers a device public key, receives an httpOnly session
cookie, and stores only client-side device metadata plus a CSRF token. Mutating
API calls include CSRF, and encrypted secret/challenge envelopes bind request,
origin, type, device id, and expiry.

Secrets are sent to the Secret Broker, not to Agent/LLM context. Challenge
answers are handled by the Challenge Relay or target browser, not by the model.
Human Takeover pauses the Agent and gives the user browser control until
release.

The PWA uses browser WebCrypto in local mode: P-256 ECDH, HKDF-SHA256, and
AES-GCM with request-bound associated data. The Python CLI uses the native
X25519 secure channel. Both envelope formats are decrypted only by the local
Broker path.

# Cloud Control Service

OmniDoer Cloud Direct Mode assumes the Linux Agent runs on a user-controlled
cloud server or VPS. Android, Windows, and PWA Control Clients connect directly
to that server over HTTPS/WSS. OmniDoer does not use a third-party relay,
Telegram, OpenAI, or any SaaS service as the control transport.

```text
Control Client
  <-> HTTPS/WSS
OmniDoer Control Service on the user's cloud server
  <-> local process / localhost / future Unix socket
Secret Broker / Challenge Relay / Human Takeover Relay / Browser Controller
  <-> Vault / headless Chromium / Agent runtime
```

Codex CLI still talks to OmniDoer through a local MCP stdio process. The MCP
server, Vault, Broker, and browser internals are not public interfaces and
should not be exposed to the internet.

Cloud Direct Mode requires explicit `--cloud-direct`, HTTPS public URL,
pairing, device identity, session auth, CSRF/origin checks, security headers,
and rate limiting. Secrets and challenge answers are encrypted in the Control
Client before submission. TLS protects transport, but Secret Broker and
Challenge Relay E2EE remain the sensitive-data boundary.

After pairing, protected Control Service APIs require both the httpOnly session
cookie and a request signature from the paired device private key. The signature
binds device id, session id, HTTP method, path, timestamp, and nonce; nonces are
single-use to reject replay. Mutating requests also require the CSRF header.

Requests may be scoped to a specific paired `device_id`. In Cloud Direct Mode,
devices only see and act on requests assigned to them, plus unassigned requests
intended for any paired device. This lets high-risk approvals or takeover
sessions be pinned to the user's phone or another trusted client.

Request push uses a signed HTTPS event stream. The PWA opens
`/api/events?stream=1` with `fetch()` so it can attach the device-signature
headers; plain `EventSource` is intentionally avoided because browsers do not
allow custom authentication headers there. Each streamed snapshot is filtered by
the authenticated device session before it leaves the Control Service.

If a website requires account registration before the Agent can continue, the
Control Service uses Registration Handoff rather than model-driven signup. The
cloud browser remains the real website session; the Control Client receives the
browser stream and sends user input events back to that session. The Agent is
paused until the user releases control, and registration secrets, verification
answers, and CAPTCHA/passkey interactions are not available to MCP or Codex.

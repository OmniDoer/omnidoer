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

Local Dev Mode is restricted to loopback and is the only mode where protected
Control APIs may be used without pairing. LAN Mode and Cloud Direct Mode both
require pairing, device identity, session auth, request/device scoping,
CSRF/origin checks, and rate limiting for mutating APIs. Cloud Direct Mode adds
explicit `--cloud-direct`, HTTPS public URL, and public-server transport
requirements. Secrets and challenge answers are encrypted in the Control Client
before submission. TLS protects transport, but Secret Broker and Challenge
Relay E2EE remain the sensitive-data boundary.

When TLS is terminated by Nginx, Caddy, Traefik, or another reverse proxy, the
proxy must forward `X-Forwarded-Proto: https` or `Forwarded: proto=https`.
OmniDoer checks that marker before pairing or serving authenticated Control API
requests in `--behind-reverse-proxy` mode. This prevents direct HTTP access to
the backend listener from acting as a Cloud Direct control path.

After pairing, protected Control Service APIs require both the httpOnly session
cookie and a request signature from the paired device private key. The signature
binds device id, session id, HTTP method, path, timestamp, and nonce; nonces are
single-use to reject replay. Mutating requests also require the CSRF header.
Device and session revocation APIs use the same mutating-request protections,
and revoking a device also revokes its active sessions.

Requests may be scoped to a specific paired `device_id`. In Cloud Direct Mode,
devices only see and act on requests assigned to them, plus unassigned requests
intended for any paired device. This lets high-risk approvals or takeover
sessions be pinned to the user's phone or another trusted client.

Request push uses WSS when available and a signed HTTPS event stream as a
compatibility fallback. Browser WebSocket connections cannot attach custom
headers, so the PWA authenticates `/api/ws/requests` with the httpOnly session
cookie plus a nonce-bound device signature in `Sec-WebSocket-Protocol`. The SSE
fallback opens `/api/events?stream=1` with `fetch()` so it can attach the same
device-signature headers; plain `EventSource` is intentionally avoided because
browsers do not allow custom authentication headers there. Each streamed
snapshot is filtered by the authenticated device session before it leaves the
Control Service.

The QR pairing URL includes a short-lived `code` and opaque `pairing_id`. Before
the user confirms pairing, the PWA can fetch public pairing metadata by
`pairing_id` so the screen shows the server URL, broker fingerprint, web broker
fingerprint, and expiry. That metadata endpoint does not return the pairing
code, code hash, session token, device private key, secret payload, challenge
answer, or vault data.

If a website requires account registration before the Agent can continue, the
Control Service uses Registration Handoff rather than model-driven signup. The
cloud browser remains the real website session; the Control Client receives the
browser stream and sends user input events back to that session. The Agent is
paused until the user releases control, and registration secrets, verification
answers, and CAPTCHA/passkey interactions are not available to MCP or Codex.
Takeover input events are allowlisted and audit logs record only event
categories, never typed text or challenge answers. Browser-frame input is
also frame-bound: the Control Service records the last delivered frame id and
capture timestamp, then rejects stale or mismatched input before forwarding it
to the browser worker. The Control Client mirrors that rule with a visible
freshness indicator and client-side stale-input refresh. Mobile users can zoom
and pan the frame projection in the PWA, but those view-only transforms do not
change the frame id binding or screenshot-pixel coordinate mapping used by the
Control Service. Two-finger pinch gestures are consumed by the PWA as local
projection zoom and are not forwarded as browser input events. If a mobile
client briefly loses frame fetch connectivity,
the PWA retains the last delivered frame for visual continuity while the
freshness guard blocks stale input until a new frame is delivered.
After accepted takeover input, the PWA triggers a short-delay frame refresh
and coalesces overlapping frame requests. This reduces perceived latency
without changing the server-side frame id binding requirement.
For lower-latency projection, Cloud Direct exposes an authenticated
`/api/ws/requests/{request_id}/frames` WebSocket stream. The stream uses the
same device subprotocol signature, request visibility checks, frame metadata,
and `record_takeover_frame` binding as the signed HTTP frame endpoint; HTTP
polling remains the fallback.
Mobile page visibility is also part of the client transport contract: hidden
PWAs pause frame polling, retain the last visible frame, and refresh
immediately when visible again. The PWA blocks takeover input while hidden or
paused, and it keeps typed handoff text in the local field unless delivery is
accepted by the Control Service.

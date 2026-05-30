# Control Client

The OmniDoer Control Client is the user control plane for tasks, credential
entry, challenge handling, approval, audit review, and Human Takeover Mode.

MVP commands:

```sh
omnidoer control serve --host 127.0.0.1 --port 8787
omnidoer control submit-task "Log in to the demo site and download my invoice"
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

In LAN Mode and Cloud Direct Mode the same PWA connects to the user's own
Control Service. A pairing URL from `omnidoer control pair --print-qr` opens
the Pair Device panel, registers a device public key, receives an httpOnly
session cookie, and stores only client-side device metadata plus a CSRF token.
Mutating API calls include CSRF, and encrypted secret/challenge envelopes bind
request, origin, type, device id, and expiry.

Secrets are sent to the Secret Broker, not to Agent/LLM context. Challenge
answers are handled by the Challenge Relay or target browser, not by the model.
Human Takeover pauses the Agent and gives the user browser control until
release.

Registration Handoff is a specialized Human Takeover request for legitimate
user account creation. The Agent opens the registration page and pauses; the
Control Client streams the browser and forwards the user's touch, keyboard, and
mouse input back to the cloud browser. After the user completes registration
and clicks Release Control, the Agent observes the resulting login state and
continues. Registration form contents, verification answers, passkeys, and
CAPTCHA interactions are never returned through MCP.

Takeover input is a control-only channel. The server accepts only a fixed set
of browser input event types (`tap`, `click`, `double_click`, `long_press`,
`drag`, `scroll`, `type`, `key`, and `release`) and rejects unknown events
without echoing user-provided text. Audit records store the event category, not
typed text, challenge answers, passkey material, or registration secrets.
Each streamed browser frame includes a frame id and capture timestamp. Touch,
keyboard, and text events sent from the Control Client are bound to the visible
frame id, and stale or mismatched frame input is rejected so a tap intended for
one page is not replayed onto a different page after navigation.
Pointer input is also checked against the viewport dimensions recorded for the
last delivered frame before it can reach the browser worker.
The Human Takeover panel displays frame freshness and blocks stale input
client-side before refreshing the projection.
On small screens the same panel can zoom the browser frame and switch to a
view-pan mode for reading dense CAPTCHA, passkey, or registration prompts.
Those controls change only the projection displayed in the PWA. Input events
remain bound to the visible frame id and are mapped back to screenshot pixel
coordinates before they reach the browser worker.
Two-finger pinch is handled locally as projection zoom, so a user trying to
inspect small challenge text does not accidentally send a tap or drag to the
remote browser.
During transient frame fetch failures, the panel keeps the last delivered
browser frame visible, shows a reconnecting stream state, and relies on frame
freshness to block stale input until the Control Service delivers a current
frame again.
Successful takeover input also schedules a fast follow-up frame refresh so
mobile users see page reactions without waiting for the next fixed polling
interval. Overlapping frame fetches are coalesced; the Control Service still
records the delivered frame id before later input can be accepted.
The PWA prefers an authenticated WebSocket takeover-frame stream when the
browser and server path support it, then falls back to signed HTTP frame
polling without changing the visible-frame binding contract.
If the mobile browser is backgrounded or the phone locks, takeover frame
polling pauses and resumes with an immediate current-frame fetch when the PWA
becomes visible again. Takeover input is blocked while the PWA is hidden or
frame polling is paused, and typed handoff text is only cleared after the
Control Service accepts delivery.

The PWA uses browser WebCrypto in local mode: P-256 ECDH, HKDF-SHA256, and
AES-GCM with request-bound associated data. The Python CLI uses the native
X25519 secure channel. Both envelope formats are decrypted only by the local
Broker path.

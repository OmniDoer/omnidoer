# Cloud Direct Deployment

Run the Control Service on your own server:

```sh
omnidoer control serve \
  --cloud-direct \
  --host 0.0.0.0 \
  --port 8787 \
  --public-url https://agent.example.com \
  --behind-reverse-proxy
```

For direct TLS termination:

```sh
omnidoer control serve \
  --cloud-direct \
  --host 0.0.0.0 \
  --port 8787 \
  --public-url https://agent.example.com:8787 \
  --tls-cert /path/fullchain.pem \
  --tls-key /path/privkey.pem
```

`0.0.0.0` is rejected unless `--cloud-direct` is explicit. Cloud Direct rejects
non-HTTPS `public-url` unless `--insecure-dev-public` is explicitly provided
for temporary testing. Non-loopback LAN mode is for trusted local networks and
still requires pairing, session auth, CSRF, origin checks, and request/device
scoping. A loopback bind with a non-local `--public-url` is rejected unless
Cloud Direct is explicit, so a reverse proxy cannot accidentally expose Local
Dev Mode. Local development can use:

When `--behind-reverse-proxy` is used, configure the proxy to send
`X-Forwarded-Proto: https` or `Forwarded: proto=https` to the OmniDoer backend.
Cloud Direct pairing and authenticated Control API requests are rejected if the
backend does not see one of those HTTPS markers.

```sh
omnidoer control serve \
  --cloud-direct \
  --host 127.0.0.1 \
  --port 8787 \
  --public-url https://localhost:8787 \
  --tls-self-signed-dev
```

Create a short-lived pairing URL:

```sh
omnidoer control pair --print-qr --expires 10m --public-url https://agent.example.com
```

Only pair devices you control. Pairing codes are one-time and short TTL. After
pairing, clients use device identity plus short-lived sessions. Protected API
requests are signed by the paired device key and replay-protected with nonces.
When the PWA opens from the QR code, it shows the server URL, pairing code,
broker fingerprint, web broker fingerprint, and expiry before the user confirms
pairing. The metadata used for that preview is public but not secret-bearing.

Request push prefers WSS on `/api/ws/requests`. The browser uses its httpOnly
session cookie plus a nonce-bound device signature in `Sec-WebSocket-Protocol`;
the server verifies Origin, HTTPS reverse-proxy markers, session status,
device revocation, signature, and replay nonce before streaming requests. A
signed HTTPS stream remains as a fallback for environments that cannot use
WebSocket.
Revoke access:

```sh
omnidoer control devices
omnidoer control revoke-device <device_id>
omnidoer control sessions
omnidoer control revoke-session <session_id>
```

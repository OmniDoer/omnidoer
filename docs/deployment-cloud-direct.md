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
for temporary testing. Local development can use:

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
Revoke access:

```sh
omnidoer control devices
omnidoer control revoke-device <device_id>
omnidoer control sessions
omnidoer control revoke-session <session_id>
```

# Pairing Security

Pairing establishes device identity; it is not a secret-submission channel.

- Pairing codes are 6-digit, time-limited, and capped-use. By default a pairing
  invite is valid for 24 hours and can pair up to 10 browsers/devices.
- `omnidoer pair` prints the 6-digit code and also renders a pairing URL as a
  real terminal QR matrix so Android, Windows, and PWA clients can scan it from
  the server console. Treat the code and QR as sensitive while they are valid.
  The lower-level `omnidoer control pair --print-qr` command remains available
  for scripts.
- Pairing creates a device record with a public key fingerprint.
- The client keeps its private key locally.
- Pairing creates a long-lived, cached, revocable session cookie for the web
  client.
- Session tokens are stored hashed and are not returned in public API payloads.
- Active sessions slide their long-term expiry forward to avoid repeated
  pairing during normal use; revoking the device or session stops access
  immediately.
- Protected Cloud Direct requests must include a device-key signature over the
  device id, session id, HTTP method, path, timestamp, and nonce.
- Signature nonces are single-use. Replayed signed requests are rejected.
- Individual control requests can be assigned to one `device_id`; other paired
  devices cannot list, open, approve, submit, or stream that request.
- CSRF tokens protect mutating HTTP requests.
- Revoked devices and sessions cannot access requests, audit metadata,
  takeover frames, approvals, or secret submission endpoints.

Secrets and challenge answers are encrypted by the Control Client for the
Secret Broker or Challenge Relay. Associated data binds `request_id`, `origin`,
`request_type`, and in Cloud Direct mode can also bind `device_id` and
`expires_at`. Replays are rejected.

# Pairing Security

Pairing establishes device identity; it is not a secret-submission channel.

- Pairing codes are short TTL and one-time use.
- `omnidoer control pair --print-qr` renders the pairing URL as a real terminal
  QR matrix so Android, Windows, and PWA clients can scan it from the server
  console. Treat this QR as sensitive while it is valid.
- Pairing creates a device record with a public key fingerprint.
- The client keeps its private key locally.
- Pairing creates a short-lived session cookie for the web client.
- Session tokens are stored hashed and are not returned in public API payloads.
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

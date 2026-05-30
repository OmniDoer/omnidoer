# Reverse Proxy

Cloud Direct Mode can run behind Nginx, Caddy, or Traefik. In that deployment,
TLS terminates at the reverse proxy and OmniDoer listens on localhost or a
private interface.

```sh
omnidoer control serve \
  --cloud-direct \
  --host 127.0.0.1 \
  --port 8787 \
  --public-url https://agent.example.com \
  --behind-reverse-proxy
```

The configured `public-url` must be HTTPS. The reverse proxy must set
`X-Forwarded-Proto: https` or a standards-compatible `Forwarded: proto=https`
header for Control Service API requests. Cloud Direct rejects sensitive API and
pairing requests behind a reverse proxy when that HTTPS marker is missing, so a
direct HTTP connection to the backend cannot bypass TLS termination policy.

WebSocket/SSE and HTTP requests must preserve the original host and scheme.
Unknown browser `Origin` values are rejected in Cloud Direct Mode. Do not proxy
MCP, Vault, Broker, or browser debugging ports to the internet.

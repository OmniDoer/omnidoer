"""Security headers for Control Service responses."""

from __future__ import annotations


SECURITY_HEADERS = {
    "content-security-policy": "default-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "x-content-type-options": "nosniff",
    "cache-control": "no-store",
}


def apply_security_headers(send_header) -> None:
    for key, value in SECURITY_HEADERS.items():
        send_header(key, value)

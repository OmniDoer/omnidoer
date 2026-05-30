"""Control Service deployment modes and Cloud Direct validation."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class ControlServiceConfig:
    host: str
    port: int
    public_url: str
    mode: str
    cloud_direct: bool = False
    behind_reverse_proxy: bool = False
    tls_cert: str | None = None
    tls_key: str | None = None
    tls_self_signed_dev: bool = False
    insecure_dev_public: bool = False

    @property
    def public_origin(self) -> str:
        parsed = urlparse(self.public_url)
        return f"{parsed.scheme}://{parsed.netloc}"


def validate_public_url(public_url: str, *, require_https: bool) -> None:
    parsed = urlparse(public_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("public-url must include scheme and host")
    if require_https and parsed.scheme != "https":
        raise ValueError("cloud direct public-url must be https")


def build_config(
    *,
    host: str,
    port: int,
    public_url: str | None = None,
    cloud_direct: bool = False,
    behind_reverse_proxy: bool = False,
    tls_cert: str | None = None,
    tls_key: str | None = None,
    tls_self_signed_dev: bool = False,
    insecure_dev_public: bool = False,
) -> ControlServiceConfig:
    if host == "0.0.0.0" and not cloud_direct:
        raise ValueError("0.0.0.0 requires explicit --cloud-direct")

    if cloud_direct:
        if not public_url:
            raise ValueError("--cloud-direct requires --public-url")
        validate_public_url(public_url, require_https=not insecure_dev_public)
        has_direct_tls = bool(tls_cert and tls_key) or tls_self_signed_dev
        if not has_direct_tls and not behind_reverse_proxy and not insecure_dev_public:
            raise ValueError("--cloud-direct requires TLS cert/key, --tls-self-signed-dev, or --behind-reverse-proxy")
        if behind_reverse_proxy:
            validate_public_url(public_url, require_https=True)
        mode = "cloud_direct"
    elif host in LOCAL_HOSTS:
        public_url = public_url or f"http://{host}:{port}"
        validate_public_url(public_url, require_https=False)
        mode = "local_dev"
    else:
        public_url = public_url or f"http://{host}:{port}"
        validate_public_url(public_url, require_https=False)
        mode = "lan"

    return ControlServiceConfig(
        host=host,
        port=port,
        public_url=public_url,
        mode=mode,
        cloud_direct=cloud_direct,
        behind_reverse_proxy=behind_reverse_proxy,
        tls_cert=tls_cert,
        tls_key=tls_key,
        tls_self_signed_dev=tls_self_signed_dev,
        insecure_dev_public=insecure_dev_public,
    )


def security_status(config: ControlServiceConfig) -> dict:
    return {
        "mode": config.mode,
        "public_url": config.public_url,
        "cloud_direct": config.cloud_direct,
        "requires_pairing": config.mode in {"lan", "cloud_direct"},
        "requires_authentication": config.mode == "cloud_direct",
        "requires_https": config.mode == "cloud_direct" and not config.insecure_dev_public,
        "behind_reverse_proxy": config.behind_reverse_proxy,
        "mcp_publicly_exposed": False,
        "vault_broker_publicly_exposed": False,
        "secret_submission_e2ee_required": True,
    }

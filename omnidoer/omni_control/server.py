"""Local HTML5/PWA Control Client server."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def static_root() -> Path:
    return Path(str(resources.files("omnidoer.omni_control") / "static"))


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from functools import partial

    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("MVP local mode only allows 127.0.0.1/localhost")
    handler = partial(SimpleHTTPRequestHandler, directory=str(static_root()))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"OmniDoer Control Client listening on http://{host}:{port}/")
    server.serve_forever()

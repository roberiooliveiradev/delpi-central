"""Local OpenAPI HTTP server for J-R4 full-chain tests."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable


class LocalOpenApiHttpServer:
    """Minimal ThreadingHTTPServer bound to 127.0.0.1:0 with controlled JSON routes."""

    def __init__(self, routes: dict[str, dict[str, Any]] | None = None):
        self._routes = dict(routes or {})
        self.hits: list[str] = []
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        if not self._httpd:
            raise RuntimeError("server not started")
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> "LocalOpenApiHttpServer":
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                path = self.path.split("?", 1)[0]
                owner.hits.append(path)
                payload = owner._routes.get(path)
                if payload is None:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error":"not_found"}')
                    return
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        self._thread = None

    def __enter__(self) -> "LocalOpenApiHttpServer":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.stop()


def make_never_seen_provider_key() -> str:
    return "acme-harbor-jr4-never-seen"

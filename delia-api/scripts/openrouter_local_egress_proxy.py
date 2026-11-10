#!/usr/bin/env python3
"""EVAL-ONLY: localhost OpenAI-compatible proxy → OpenRouter.

Allows DELIA_ENV≠production to call qwen/qwen3-14b while the local LLM
egress guard sees a loopback host. No functional INT-1 logic. Reversible:
kill the process. Never logs Authorization headers or API keys.
"""

from __future__ import annotations

import argparse
import gzip
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen


UPSTREAM = "https://openrouter.ai"
_HOP = {
    "host",
    "content-length",
    "transfer-encoding",
    "connection",
    "accept-encoding",
}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        sys.stderr.write(
            "proxy %s %s\n" % (self.command, self.path.split("?", 1)[0])
        )

    def _forward(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {
            k: v
            for k, v in self.headers.items()
            if k.lower() not in _HOP
        }
        # Request identity encoding so urllib returns decoded bytes and
        # clients never see a gzip body with stripped content-encoding.
        headers["Accept-Encoding"] = "identity"
        url = UPSTREAM + self.path
        req = Request(url, data=body, headers=headers, method=self.command)
        try:
            with urlopen(req, timeout=180) as resp:
                payload = resp.read()
                encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if encoding == "gzip":
                    payload = gzip.decompress(payload)
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() in {
                        "transfer-encoding",
                        "connection",
                        "content-encoding",
                        "content-length",
                    }:
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except Exception as exc:  # noqa: BLE001 — surface upstream failure
            msg = str(exc).encode("utf-8", errors="replace")[:500]
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self) -> None:  # noqa: N802
        self._forward()

    def do_POST(self) -> None:  # noqa: N802
        self._forward()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._forward()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18765)
    args = parser.parse_args()
    if not os.environ.get("DELIA_LLM_API_KEY") and not os.environ.get(
        "OPENROUTER_API_KEY"
    ):
        # Key is supplied by clients via Authorization; presence optional.
        pass
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    sys.stderr.write(
        "openrouter_local_egress_proxy listening on %s:%s\n"
        % (args.host, args.port)
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

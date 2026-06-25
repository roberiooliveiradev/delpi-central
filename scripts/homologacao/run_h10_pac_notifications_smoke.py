#!/usr/bin/env python3
"""Smoke H10 — notificações PAC (dry-run + dispatch opcional)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _base_url() -> str:
    return (os.environ.get("BASE_URL") or "http://localhost/apps/api-delpi").rstrip("/")


def _token() -> str:
    token = (
        os.environ.get("TOKEN")
        or os.environ.get("API_DELPI_INTERNAL_SERVICE_TOKEN")
        or ""
    ).strip()
    if not token:
        raise SystemExit("Defina TOKEN ou API_DELPI_INTERNAL_SERVICE_TOKEN")
    return token


def _request(method: str, path: str, *, dry_run: bool) -> dict:
    url = f"{_base_url()}{path}"
    if dry_run:
        url = f"{url}?dry_run=true"
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
        data=b"{}",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def main() -> int:
    live = "--live" in sys.argv
    try:
        dry = _request(
            "POST",
            "/quality/action-plans/notifications/dispatch",
            dry_run=True,
        )
        print("dry_run:", json.dumps(dry.get("data") or dry, ensure_ascii=False))
        if not dry.get("success", True):
            print("Falha no dry-run", file=sys.stderr)
            return 1
        if live:
            live_result = _request(
                "POST",
                "/quality/action-plans/notifications/dispatch",
                dry_run=False,
            )
            print("live:", json.dumps(live_result.get("data") or live_result, ensure_ascii=False))
            if not live_result.get("success", True):
                return 1
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

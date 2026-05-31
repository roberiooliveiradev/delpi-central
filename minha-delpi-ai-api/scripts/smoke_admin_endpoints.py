#!/usr/bin/env python3
"""Smoke — login Keycloak + endpoints admin (Minha DELPI Chat)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_API_PREFIX = os.environ.get("SMOKE_AI_PREFIX", "/apps/minha-delpi-ai/api").strip()


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _request(
    method: str,
    path: str,
    *,
    token: str,
    body: dict | None = None,
    timeout: int = 120,
) -> dict | list:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(
        f"{_BASE_URL}{_API_PREFIX}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
        print("OK login Keycloak")
    except (urllib.error.URLError, RuntimeError) as err:
        print(f"FAIL login: {err}", file=sys.stderr)
        return 1

    checks: list[tuple[str, str, str | None]] = [
        ("GET", "/admin/knowledge/documents?limit=1", "summary"),
        ("GET", "/admin/guidelines", None),
        ("GET", "/admin/metrics/summary?hours=24", "sessions"),
        ("GET", "/admin/agents/specialized", None),
        ("GET", "/admin/responses/evaluations/summary", "total"),
    ]

    for method, path, required_key in checks:
        try:
            payload = _request(method, path, token=token)
            if required_key and isinstance(payload, dict) and required_key not in payload:
                print(f"FAIL {path}: sem campo {required_key}", file=sys.stderr)
                failed += 1
            else:
                print(f"OK {method} {path}")
        except urllib.error.HTTPError as err:
            print(f"FAIL {path}: HTTP {err.code}", file=sys.stderr)
            failed += 1
        except urllib.error.URLError as err:
            print(f"FAIL {path}: {err}", file=sys.stderr)
            failed += 1

    try:
        simulate = _request(
            "POST",
            "/admin/agent/simulate",
            token=token,
            body={"question": "oi"},
            timeout=180,
        )
        if not isinstance(simulate, dict) or "answerPreview" not in simulate:
            print("FAIL simulate: resposta inesperada", file=sys.stderr)
            failed += 1
        else:
            print("OK POST /admin/agent/simulate")
    except urllib.error.HTTPError as err:
        print(f"FAIL simulate: HTTP {err.code}", file=sys.stderr)
        failed += 1
    except urllib.error.URLError as err:
        print(f"FAIL simulate: {err}", file=sys.stderr)
        failed += 1

    if failed:
        print(f"\n{failed} falha(s)", file=sys.stderr)
        return 1

    print("\nSmoke admin: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

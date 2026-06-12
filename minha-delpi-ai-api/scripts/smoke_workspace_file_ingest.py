#!/usr/bin/env python3
"""Smoke — política de ingestão unificada (Playbook 17).

Valida GET /chat/ingest/policy para todas as famílias e matriz de extensões.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_workspace_file_ingest.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 ...
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.workspace_file_ingest_policy_service import (
    WorkspaceFileIngestPolicyService,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_FAMILIES = (
    "session_attachment",
    "agent_source",
    "project_source",
    "global_knowledge",
    "context_paste",
)


def _request(method: str, url: str, *, token: str | None = None) -> dict:
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def _fetch_token() -> str:
    token_url = (
        f"{_BASE_URL}/realms/{_REALM}/protocol/openid-connect/token"
    )
    body = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        token_url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError("Token endpoint did not return access_token")

    return str(token)


def main() -> int:
    token = _fetch_token()
    api_base = f"{_BASE_URL}{_CHAT_PREFIX}"

    for family in _FAMILIES:
        payload = _request(
            "GET",
            f"{api_base}/ingest/policy?family={urllib.parse.quote(family)}",
            token=token,
        )

        expected_extensions = sorted(
            WorkspaceFileIngestPolicyService.allowed_extensions(family)
        )

        if payload.get("family") != family:
            print(f"FAIL {family}: family mismatch {payload!r}", file=sys.stderr)
            return 1

        if payload.get("extensions") != expected_extensions:
            print(
                f"FAIL {family}: extensions mismatch "
                f"api={payload.get('extensions')} expected={expected_extensions}",
                file=sys.stderr,
            )
            return 1

        if payload.get("maxSizeBytes") != WorkspaceFileIngestPolicyService.max_size_bytes(
            family
        ):
            print(f"FAIL {family}: maxSizeBytes mismatch", file=sys.stderr)
            return 1

        print(f"OK {family}: {len(expected_extensions)} extensões")

    if not WorkspaceFileIngestPolicyService.is_extension_allowed("agent_source", "foto.png"):
        print("OK F2-matrix: agente rejeita .png")
    else:
        print("FAIL F2-matrix: agente deveria rejeitar .png", file=sys.stderr)
        return 1

    print("Smoke Playbook 17 — ingest policy: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

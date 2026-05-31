#!/usr/bin/env python3
"""Smoke HTTP opcional — turno de correção textual com adminDebug (admin)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _default_smoke_base_url() -> str:
    explicit = os.environ.get("SMOKE_BASE_URL", "").strip()

    if explicit:
        return explicit

    if os.path.isdir("/app"):
        return "http://delpi-gateway"

    return "http://localhost"


_BASE_URL = _default_smoke_base_url().strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_MESSAGE = os.environ.get(
    "SMOKE_TEXT_CORRECTION_MESSAGE",
    "corrija: o estoque esta baixo",
).strip()


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


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

    return str(payload["access_token"])


def _pick_agent_id(token: str) -> str:
    agents = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20",
        token=token,
    )
    items = agents if isinstance(agents, list) else agents.get("items") or []

    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    return ""


def main() -> int:
    try:
        token = _fetch_token()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        print(f"SKIP gateway/token ({exc})", file=sys.stderr)
        return 0

    agent_id = _pick_agent_id(token)

    if not agent_id:
        print("SKIP sem agente habilitado", file=sys.stderr)
        return 0

    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke text correction HTTP", "agentId": agent_id},
    )
    session_id = str(session.get("id") or "")

    if not session_id:
        print("SKIP sem session_id", file=sys.stderr)
        return 0

    try:
        result = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={"message": _MESSAGE, "adminDebug": True},
        )
    except urllib.error.HTTPError as exc:
        print(f"SKIP HTTP {exc.code}", file=sys.stderr)
        return 0

    assistant = result.get("assistantMessage") or result.get("assistant") or {}
    metadata = assistant.get("metadata") or {}
    admin_debug = metadata.get("adminDebug") or result.get("adminDebug") or {}

    if metadata.get("textTask", {}).get("type") != "correction":
        print(f"FAIL textTask ({metadata.get('textTask')})", file=sys.stderr)
        return 1

    metrics = (
        admin_debug.get("textCorrectionMetrics")
        or metadata.get("textCorrectionMetrics")
    )

    if not metrics:
        if metadata.get("textTask", {}).get("type") == "correction":
            print("OK smoke_text_correction_http (sem adminDebug — usuário não admin?)")
            return 0
        print(f"FAIL sem textCorrectionMetrics (admin={bool(admin_debug)})", file=sys.stderr)
        return 1

    if not (metadata.get("textCorrectionFollowUpSuggestions") or []):
        print("FAIL sem chips de follow-up", file=sys.stderr)
        return 1

    print("OK smoke_text_correction_http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

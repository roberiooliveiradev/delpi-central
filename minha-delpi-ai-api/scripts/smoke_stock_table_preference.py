#!/usr/bin/env python3
"""Smoke — estoque com preferência de tabela (consulta real + metadata)."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10080001").strip()


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=300) as response:
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

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "context": "geral"},
    )
    return str(payload["id"])


def _send(token: str, session_id: str, agent_id: str, message: str, *, response_format: str | None = None) -> dict:
    body = {"message": message, "agentId": agent_id}

    if response_format:
        body["responseFormat"] = response_format

    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _stock_meta(response: dict) -> dict | None:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()

        if "/stock" in path and meta.get("ok"):
            return meta

    return None


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
        print("OK login")
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = _first_agent(token)
    session_id = _create_session(token, agent_id)
    print(f"OK sessão {session_id}")

    message = f"estoque do produto {_PRODUCT}"

    resp = _send(token, session_id, agent_id, message, response_format="table")
    meta = _stock_meta(resp)

    if not meta:
        print("FAIL sem toolCall de estoque", file=sys.stderr)
        return 1

    preferred = str(meta.get("preferredFormat") or "")
    decision = meta.get("presentationDecision") or {}
    selected = str(decision.get("selected") or "")
    presentation = meta.get("presentation") or {}
    presentation_type = str(presentation.get("type") or "")

    print(f"OK stock path={meta.get('path')}")
    print(f"   preferredFormat={preferred!r} selected={selected!r} presentation={presentation_type!r}")

    if preferred != "table" or selected != "table":
        print("FAIL preferência tabela não refletida no metadata", file=sys.stderr)
        failed += 1

    if presentation_type != "table":
        print("FAIL componente primário não é tabela", file=sys.stderr)
        failed += 1

    rows = presentation.get("rows") or []

    if not rows:
        tables = meta.get("tablePresentations") or []
        for table in tables:
            if isinstance(table, dict) and table.get("rows"):
                rows = table["rows"]
                break

    if not rows:
        print("WARN sem linhas de estoque no metadata (pode ser produto sem saldo)", file=sys.stderr)
    else:
        print(f"OK {len(rows)} linha(s) de estoque no metadata")

    if "/system/tables" in str(meta.get("path") or ""):
        print("FAIL rota errada /system/tables", file=sys.stderr)
        failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

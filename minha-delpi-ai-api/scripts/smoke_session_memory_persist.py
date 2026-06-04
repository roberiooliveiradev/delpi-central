#!/usr/bin/env python3
"""Smoke — memória persistida Fase 4 (reload de overlay + clear).

Uso:
  PYTHONPATH=/app python scripts/smoke_session_memory_persist.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from uuid import UUID

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


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
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente")


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke memória persistida", "agentId": agent_id},
    )
    return str(payload["id"])


def _send(token: str, session_id: str, agent_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def _clear_memory(token: str, session_id: str) -> int:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/memory/clear",
        token=token,
        body={},
    )
    return int(payload.get("cleared") or 0)


def _tool_path_has_product(response: dict, code: str) -> bool:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")
        args = call.get("arguments") or meta.get("parameters") or {}
        if code in path or str(args).find(code) >= 0:
            return True
    return False


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
        print("OK login: token obtido")
    except Exception as exc:
        print(f"SKIP login: {exc}", file=sys.stderr)
        return 0

    agent_id = _first_agent(token)
    session_id = _create_session(token, agent_id)

    bootstrap = _send(token, session_id, agent_id, "me fale do produto 10080001")
    admin = bootstrap.get("adminDebug") or {}
    memory = admin.get("memory") or {}
    entities = memory.get("operationalFocus") or {}

    if entities.get("productCode") == "10080001" or _tool_path_has_product(
        bootstrap, "10080001"
    ):
        print("OK turno 1: memória ativa com productCode (adminDebug ou tool)")
        metrics = bootstrap.get("sessionMemoryMetrics") or admin.get("sessionMemoryMetrics")
        if metrics:
            print(f"OK sessionMemoryMetrics snapshot ({metrics.get('resolvedReferenceCount', 0)} refs)")
    else:
        print(f"FAIL turno 1: operationalFocus={entities!r}", file=sys.stderr)
        failed += 1

    follow = _send(token, session_id, agent_id, "mostre os fornecedores")

    if _tool_path_has_product(follow, "10080001"):
        print("OK turno 2: follow-up reutilizou produto 10080001")
    else:
        print(f"WARN turno 2: toolCalls={follow.get('toolCalls')}", file=sys.stderr)

    cleared = _clear_memory(token, session_id)
    print(f"OK memory/clear: cleared={cleared}")

    after_clear = _send(token, session_id, agent_id, "mostre os fornecedores")
    admin_after = after_clear.get("adminDebug") or {}
    memory_dbg = admin_after.get("memory") or {}
    entities_after = memory_dbg.get("operationalFocus") or {}

    if memory_dbg.get("clearedThisTurn"):
        print("OK turno 3: após clear, turno marca persistedMemoryCleared")
    elif entities_after.get("productCode") != "10080001":
        print("OK turno 3: após clear, sem productCode na memória ativa")
    else:
        print(
            f"WARN turno 3: productCode ainda em operationalFocus "
            f"(pode vir de tool/histórico): {entities_after!r}",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

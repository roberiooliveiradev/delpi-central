#!/usr/bin/env python3
"""Smoke — tarefa textual pura não dispara tools (Playbook textos Fase 2).

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_text_task_routing.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_TEXT_MESSAGE = "corrija: segue em anexo os documento solicitado"


def _request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


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


def _first_official_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke text task", "agentId": agent_id},
    )
    session_id = payload.get("id")
    if not session_id:
        raise RuntimeError(f"Sessão inválida: {payload}")
    return str(session_id)


def _send_message(token: str, session_id: str, message: str, agent_id: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )


def main() -> int:
    failed = 0

    if not ChatTextTaskIntentService.is_pure_text_task(_TEXT_MESSAGE):
        print("FAIL unit: mensagem de correção deveria ser text_task pura", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: correção classificada como text_task pura")

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 1 if failed else 0

    agent_id = _first_official_agent(token)
    session_id = _create_session(token, agent_id)
    response = _send_message(token, session_id, _TEXT_MESSAGE, agent_id)

    tool_calls = response.get("toolCalls") or []
    admin_debug = response.get("adminDebug") or {}
    pipeline = (admin_debug.get("intelligence") or {}).get("pipeline") or {}
    stages = pipeline.get("stages") or []

    if tool_calls:
        print(f"FAIL API: text_task não deveria chamar tools ({len(tool_calls)} calls)", file=sys.stderr)
        failed += 1
    else:
        print("OK API: sem toolCalls em correção textual")

    if "text_task" in stages:
        print(f"OK API: pipeline stages={stages}")
    elif stages and "tools" not in stages:
        print(f"WARN API: stages sem text_task explícito: {stages}", file=sys.stderr)
    else:
        print(f"FAIL API: pipeline operacional em text_task: {stages}", file=sys.stderr)
        failed += 1

    answer = str(response.get("answer") or "").strip()
    if not answer:
        print("FAIL API: resposta vazia", file=sys.stderr)
        failed += 1
    else:
        print("OK API: resposta textual recebida")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

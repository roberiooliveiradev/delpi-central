#!/usr/bin/env python3
"""Smoke — roteamento operacional vs capacidades (regressão homologação).

Valida que perguntas de estoque disparam tool/API e não o atalho «Sobre esta consulta».

Uso:
  PYTHONPATH=/app python scripts/smoke_operational_routing.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.application.services.chat_capabilities_service import ChatCapabilitiesService

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_STOCK_MESSAGE = "qual o estoque do produto 90260015?"
_CAPABILITY_MARKERS = ("sobre esta consulta", "se eu consigo executar", "nao que eu execute agora")


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
        body={"title": "Smoke roteamento operacional", "agentId": agent_id},
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


def _validate_unit() -> list[str]:
    errors: list[str] = []

    if ChatCapabilitiesService.is_capability_inquiry(_STOCK_MESSAGE):
        errors.append("unit: estoque com produto não deve ser capability inquiry")

    answer = ChatCapabilitiesService.resolve_capability_answer(
        message=_STOCK_MESSAGE,
        workspace_context={"agent": {"name": "Test"}, "agentId": "x"},
        allowed_action_ids=["act.stock"],
        action_catalog=[
            {
                "actionId": "act.stock",
                "method": "GET",
                "path": "/products/{code}/stock",
            }
        ],
    )

    if answer:
        errors.append(f"unit: resolve_capability_answer deveria ser None, obteve: {answer[:80]!r}")

    return errors


def main() -> int:
    failed = 0

    unit_errors = _validate_unit()
    if unit_errors:
        failed += len(unit_errors)
        for error in unit_errors:
            print(f"FAIL unit: {error}", file=sys.stderr)
    else:
        print("OK unit: estoque não roteado para capacidades")

    try:
        token = _fetch_token()
    except Exception as exc:
        detail = str(exc)
        if "502" in detail or "503" in detail or "504" in detail:
            print(f"FAIL API (infra indisponível): {exc}", file=sys.stderr)
            return 1
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 1 if unit_errors else 0

    agent_id = _first_official_agent(token)
    session_id = _create_session(token, agent_id)
    response = _send_message(token, session_id, _STOCK_MESSAGE, agent_id)

    answer_lower = str(response.get("answer") or "").lower()
    tool_calls = response.get("toolCalls") or []
    admin_debug = response.get("adminDebug") or {}

    if any(marker in answer_lower for marker in _CAPABILITY_MARKERS):
        print(f"FAIL API: resposta de capacidades: {answer_lower[:200]!r}", file=sys.stderr)
        failed += 1
    else:
        print("OK API: resposta não é atalho de capacidades")

    stock_tool = False
    for call in tool_calls:
        if call.get("name") != "execute_external_action":
            continue
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()
        if "/stock" in path or "estoque" in path:
            stock_tool = True
            break

    if stock_tool:
        print("OK API: toolCalls inclui consulta de estoque")
    else:
        print(f"WARN API: toolCalls sem stock explícito ({len(tool_calls)} calls)", file=sys.stderr)

    pipeline = (admin_debug.get("intelligence") or {}).get("pipeline") or {}
    stages = pipeline.get("stages") or []

    if "capabilities" in stages and "tools" not in stages:
        print(f"FAIL API: pipeline stages={stages}", file=sys.stderr)
        failed += 1
    elif "tools" in stages or stock_tool:
        print(f"OK API: pipeline stages={stages}")
    else:
        print(f"WARN API: stages={stages}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

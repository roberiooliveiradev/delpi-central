#!/usr/bin/env python3
"""Smoke — «qual a tabela de produtos?» roteia para /system/tables/search."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_MESSAGE = "qual a tabela de produtos?"
_SYSTEM_ACTIONS = [
    {
        "actionId": "tables-search",
        "method": "GET",
        "path": "/system/tables/search",
        "operationId": "search_tables",
        "summary": "Buscar tabelas",
        "parametersSchema": [{"name": "description", "in": "query"}],
    },
]


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self.actions

    def list_actions(self):
        return self.actions


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


def _validate_unit() -> list[str]:
    service = ExternalActionSelectionService(_FakeRepository(_SYSTEM_ACTIONS))
    selected = service.select_action(
        _MESSAGE,
        allowed_action_ids=["tables-search"],
    )
    errors: list[str] = []

    if not selected:
        errors.append("unit: select_action retornou None")
        return errors

    action_id = (selected.get("arguments") or {}).get("actionId")
    params = (selected.get("arguments") or {}).get("parameters") or {}

    if action_id != "tables-search":
        errors.append(f"unit: actionId={action_id!r}")

    if params.get("description") != "produtos":
        errors.append(f"unit: description={params.get('description')!r}")

    return errors


def _first_enabled_agent(token: str) -> str:
    request = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    items = payload if isinstance(payload, list) else payload.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente habilitado")


def _validate_chat_e2e(token: str) -> list[str]:
    errors: list[str] = []
    agent_id = _first_enabled_agent(token)
    session_body = json.dumps({"title": "Smoke system tables", "agentId": agent_id}).encode()
    session_request = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        data=session_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(session_request, timeout=60) as response:
        session_id = str(json.loads(response.read().decode("utf-8"))["id"])

    message_body = json.dumps({"message": _MESSAGE, "agentId": agent_id}).encode()
    message_request = urllib.request.Request(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        data=message_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(message_request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))

    tool_calls = payload.get("toolCalls") or []
    system_call = None

    for call in tool_calls:
        if call.get("name") != "execute_external_action":
            continue

        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()

        if "/system/tables/search" in path:
            system_call = call
            break

    if not system_call:
        errors.append("chat: toolCalls sem /system/tables/search")
        return errors

    args = system_call.get("arguments") or {}
    params = args.get("parameters") or {}

    if params.get("description") != "produtos":
        errors.append(f"chat: parameters={params!r}")

    sub_intent = ((payload.get("adminDebug") or {}).get("intentRoute") or {}).get("subIntent")

    if sub_intent != "system_metadata":
        errors.append(f"chat: subIntent={sub_intent!r}")

    meta = system_call.get("metadata") or {}

    if meta.get("ok"):
        print("OK chat: tool executada com sucesso")
    else:
        print(
            "OK chat: roteamento e tool corretos "
            f"(execução ok={meta.get('ok')}, status={meta.get('statusCode')})"
        )

    return errors


def main() -> int:
    failed = 0

    unit_errors = _validate_unit()
    if unit_errors:
        failed += len(unit_errors)
        for error in unit_errors:
            print(f"FAIL {error}", file=sys.stderr)
    else:
        print("OK unit: /system/tables/search com description=produtos")

    try:
        token = _fetch_token()
        print("OK login Keycloak")
    except Exception as exc:
        print(f"SKIP API (login): {exc}", file=sys.stderr)
        return 1 if failed else 0

    # API-delpi: rota existe (pode falhar se SQL Server indisponível)
    api_path = "/apps/api-delpi/system/tables/search?description=produto&page=1&limit=3"
    try:
        request = urllib.request.Request(
            f"{_BASE_URL}{api_path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("success") is True or isinstance(payload.get("data"), list):
            print(f"OK API: GET {api_path}")
        else:
            print(f"WARN API: resposta inesperada {str(payload)[:120]}", file=sys.stderr)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in {400, 500, 503} and ("banco" in body.lower() or "timeout" in body.lower()):
            print(f"WARN API: rota alcançada, DB indisponível (HTTP {exc.code})", file=sys.stderr)
        else:
            print(f"FAIL API: HTTP {exc.code} {body[:200]}", file=sys.stderr)
            failed += 1

    chat_errors = _validate_chat_e2e(token)

    if chat_errors:
        failed += len(chat_errors)

        for error in chat_errors:
            print(f"FAIL {error}", file=sys.stderr)
    else:
        print("OK chat: intent system_metadata + tool /system/tables/search")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

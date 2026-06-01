#!/usr/bin/env python3
"""Smoke — «pesquise na web» dispara web_search, não /products/search.

Requer PYTHONPATH=/app. HTTP: SMOKE_BASE_URL=http://gateway SMOKE_USER=rober SMOKE_PASSWORD=1234
Com pesquisa web ativa: CHAT_WEB_SEARCH_ENABLED=true no container da API.
"""

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

_WEB_MESSAGE = os.environ.get(
    "SMOKE_WEB_MESSAGE",
    "pesquise na web sobre Delpi Conexões Elétricas",
).strip()


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
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
    req = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _first_agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def main() -> int:
    from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
    from app.domain.services.tool_selection_service import ToolSelectionService
    from app.infrastructure.config.settings import Settings

    if not ChatWebSearchIntentService.matches(_WEB_MESSAGE):
        print("FAIL unit: mensagem não reconhecida como web", file=sys.stderr)
        return 1
    print("OK unit: gatilho de pesquisa na web")

    from app.main import app

    with app.app_context():
        if not ChatWebSearchIntentService.blocks_external_action_selection(_WEB_MESSAGE):
            print("FAIL unit: não bloqueia actions externas", file=sys.stderr)
            return 1
        print("OK unit: bloqueia actions OpenAPI")

        enabled = ChatWebSearchIntentService.is_feature_enabled()
        print(
            f"INFO: CHAT_WEB_SEARCH_ENABLED={Settings.CHAT_WEB_SEARCH_ENABLED!r} "
            f"resolved={enabled}"
        )

        if enabled:
            tools = ToolSelectionService().select_tools(_WEB_MESSAGE)
            if not any(t.get("name") == "web_search" for t in tools):
                print(f"FAIL unit: tools sem web_search ({tools})", file=sys.stderr)
                return 1
            print("OK unit: ToolSelectionService inclui web_search")
        else:
            resolved = ChatWebSearchIntentService.resolve(_WEB_MESSAGE)
            if resolved is not None:
                print(f"FAIL unit: resolve deveria ser None ({resolved})", file=sys.stderr)
                return 1
            print("OK unit: feature off — resolve None (sem product search)")

    try:
        token = _fetch_token()
        print("OK login Keycloak")
    except Exception as exc:
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 0

    agent_id = _first_agent_id(token)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke web search", "agentId": agent_id},
    )

    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
        token=token,
        body={"message": _WEB_MESSAGE, "agentId": agent_id},
    )

    tool_calls = response.get("toolCalls") or []
    paths = []
    names = []
    for call in tool_calls:
        names.append(str(call.get("name") or ""))
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")
        if path:
            paths.append(path.lower())

    if any("/products/search" in path for path in paths):
        print(f"FAIL API: buscou produtos ERP ({paths})", file=sys.stderr)
        return 1
    print("OK API: não usou /products/search")

    intent_route = (response.get("adminDebug") or {}).get("intentRoute") or {}
    if intent_route.get("decision") != "web_search":
        print(f"WARN API: decision={intent_route.get('decision')!r}", file=sys.stderr)

    if enabled:
        if "web_search" not in names:
            print(f"FAIL API: sem tool web_search ({names})", file=sys.stderr)
            return 1
        print("OK API: executou web_search")
    else:
        if names and "execute_external_action" in names:
            print(f"FAIL API: actions externas com feature off ({names})", file=sys.stderr)
            return 1
        content = str(response.get("content") or "")
        if "pesquisa na web" not in content.lower() and "não está habilitada" not in content.lower():
            print("WARN API: resposta sem aviso explícito de feature desabilitada", file=sys.stderr)
        else:
            print("OK API: aviso de pesquisa web desabilitada (sem ERP)")

    print("Smoke pesquisa na web: verificações concluídas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

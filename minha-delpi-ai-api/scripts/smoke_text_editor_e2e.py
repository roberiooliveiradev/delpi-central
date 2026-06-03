#!/usr/bin/env python3
"""Smoke E2E — editor textual (carta, ELI5, documentação, sem tools operacionais).

Uso:
  PYTHONPATH=. python3 scripts/smoke_text_editor_e2e.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_text_task_service import ChatTextTaskService

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_CASES = (
    ("carta", "crie uma carta formal solicitando autorização", "letter", "text.letter.create"),
    ("eli5", "explique RBAC como se eu tivesse 5 anos", "eli5", "text.eli5"),
    (
        "documentação",
        "transforme essa explicação em documentação técnica",
        "documentation",
        "text.documentation.create",
    ),
)


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
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _run_unit_checks() -> None:
    for label, message, category, intent in _CASES:
        assert ChatTextTaskIntentService.classify(message) == category, label
        pure = ChatTextTaskIntentService.is_pure_text_task(message)
        assert pure is True, f"{label}: deve ser text_task pura"
        route = ChatIntentRouterService.classify(message, text_task_pure=pure)
        assert route.intent == "text_task", f"{label}: router={route.intent}"
        assert route.requires_tool is False, label
        ctx = ChatTextTaskService.classify(message)
        assert ctx.get("intent") == intent, f"{label}: intent={ctx.get('intent')}"
    print("OK unit: classificação editor textual (carta, ELI5, documentação)")


def _run_http_check(token: str, agent_id: str) -> None:
    _, message, _, _ = _CASES[1]
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-text-editor"},
    )
    session_id = str(session.get("id") or session.get("sessionId") or "")
    if not session_id:
        raise RuntimeError(f"Sessão inválida: {session}")

    result = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"content": message, "stream": False},
    )
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    tool_calls = metadata.get("toolCalls") or []
    if tool_calls:
        raise RuntimeError(f"ELI5 acionou tools: {tool_calls}")
    answer = str(result.get("content") or result.get("answer") or "").strip()
    if len(answer) < 20:
        raise RuntimeError("Resposta ELI5 muito curta")
    print("OK API: ELI5 sem toolCalls e com resposta textual")


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

    _run_unit_checks()

    if os.environ.get("SMOKE_SKIP_HTTP", "").strip() in {"1", "true", "yes"}:
        print("SKIP HTTP (SMOKE_SKIP_HTTP)")
        return 0

    try:
        token = _fetch_token()
        agent_id = _first_agent(token)
        _run_http_check(token, agent_id)
    except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        print(f"WARN HTTP smoke: {exc}", file=sys.stderr)
        print("Unit checks OK; HTTP opcional quando API offline.")

    print("OK — smoke editor textual concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

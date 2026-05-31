#!/usr/bin/env python3
"""Smoke — escrita de e-mail (text_task + email_writing, sem tools).

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_email_writing.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.application.services.chat_text_task_composer_service import (
    ChatTextTaskComposerService,
)
from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

_MIXED_MESSAGE = "consulte estoque do produto 10080001 e escreva um e-mail para compras"

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_EMAIL_MESSAGE = (
    "escreva um e-mail formal para Robério sobre criar uma IA para Minha DELPI"
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


def _first_official_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def main() -> int:
    if not ChatTextTaskIntentService.is_pure_text_task(_EMAIL_MESSAGE):
        print("FAIL unit: e-mail deveria ser text_task puro", file=sys.stderr)
        return 1

    if not ChatEmailIntentService.is_email_writing(_EMAIL_MESSAGE):
        print("FAIL unit: deveria ativar email_writing", file=sys.stderr)
        return 1

    print("OK unit: intent e-mail")

    if not ChatTextTaskIntentService.is_mixed_text_and_operational(_MIXED_MESSAGE):
        print("FAIL unit: pedido misto estoque+e-mail", file=sys.stderr)
        return 1

    mixed = ChatTextTaskComposerService.build_supplement_for_mixed_turn(
        message=_MIXED_MESSAGE,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080001/stock",
                    "humanizedSummary": {
                        "titulo": "Estoque do produto",
                        "linhas": ["Filial 01: 100 un."],
                    },
                },
            }
        ],
    )

    if not mixed or "Fonte dos dados" not in mixed:
        print("FAIL unit: rascunho operacional sem fonte", file=sys.stderr)
        return 1

    print("OK unit: e-mail operacional misto")

    try:
        token = _fetch_token()
        agent_id = _first_official_agent(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"agentId": agent_id, "title": "smoke-email"},
        )
        session_id = str(session.get("id") or session.get("sessionId") or "")
        if not session_id:
            print(f"WARN API: sessão sem id: {session}", file=sys.stderr)
            return 0

        result = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={"message": _EMAIL_MESSAGE, "agentId": agent_id},
        )
        metadata = result.get("metadata") or {}
        tool_calls = result.get("toolCalls") or metadata.get("toolCalls") or []

        if tool_calls:
            print(f"FAIL API: e-mail não deveria chamar tools ({len(tool_calls)})", file=sys.stderr)
            return 1

        stages = (metadata.get("intelligence") or {}).get("pipeline", {}).get("stages") or []
        if "text_task" in stages or "email_writing" in stages:
            print(f"OK API: pipeline {stages}")
        else:
            print(f"WARN API: stages sem text_task/email_writing: {stages}", file=sys.stderr)

        suggestions = metadata.get("emailFollowUpSuggestions") or []
        if len(suggestions) >= 3:
            print(f"OK API: {len(suggestions)} chips de refinamento")
        else:
            print("WARN API: emailFollowUpSuggestions ausente ou curto", file=sys.stderr)

        content = str(result.get("content") or "")
        if "[seu nome]" in content.lower() or "[Seu nome]" in content:
            print("OK API: placeholder de assinatura")
        elif "roberto silva" in content.lower():
            print("FAIL API: assinatura inventada", file=sys.stderr)
            return 1
        else:
            print("WARN API: assinatura não verificada automaticamente")

        print("OK smoke e-mail")
        return 0
    except urllib.error.URLError as exc:
        print(f"SKIP API (gateway indisponível): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

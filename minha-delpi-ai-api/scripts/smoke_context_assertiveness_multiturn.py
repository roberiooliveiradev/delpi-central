#!/usr/bin/env python3
"""Smoke — assertividade contextual em conversa multi-turno (Fase 5).

Valida:
  - unit: follow-up reutiliza entidade e pontua bem
  - API (opcional): metadata.contextAssertiveness na 2ª mensagem

Uso:
  PYTHONPATH=/app python scripts/smoke_context_assertiveness_multiturn.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.chat_context_assertiveness_service import (
    ChatContextAssertivenessService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService

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
        body={"title": "Smoke assertividade multiturn", "agentId": agent_id},
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


def _list_messages(token: str, session_id: str) -> list[dict]:
    payload = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    if isinstance(payload, list):
        return payload
    return list(payload.get("items") or [])


def _validate_unit_multiturn() -> list[str]:
    errors: list[str] = []
    previous = [
        {"role": "user", "content": "me fale do produto 10080001"},
        {
            "role": "assistant",
            "content": "Produto 10080001.",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"path": "/products/10080001/analyser", "ok": True},
                    }
                ]
            },
        },
    ]
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="me fale do produto 10080001",
        previous_messages=previous,
        tool_calls=previous[-1]["metadata"]["toolCalls"],
        pre_snapshot=None,
    )
    follow_snapshot = dict(snapshot)
    follow_snapshot["followUpDetected"] = True

    result = ChatContextAssertivenessService.evaluate_turn(
        message="agora estoque",
        answer="Estoque do produto.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"path": "/products/10080001/stock", "ok": True},
            }
        ],
        snapshot=follow_snapshot,
    )

    if "follow_up_entity_reused" not in result.get("flags", []):
        errors.append(f"unit: esperado follow_up_entity_reused, obteve {result}")

    if float(result.get("score", 0)) < 80:
        errors.append(f"unit: score baixo no follow-up correto: {result}")

    bad = ChatContextAssertivenessService.evaluate_turn(
        message="agora fornecedores",
        answer="Ok.",
        tool_calls=[],
        snapshot=follow_snapshot,
    )

    if "follow_up_without_entity_reuse" not in bad.get("flags", []):
        errors.append(f"unit: esperado follow_up_without_entity_reuse, obteve {bad}")

    return errors


def _latest_assistant_assertiveness(messages: list[dict]) -> dict | None:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue

        metadata = message.get("metadata") or {}
        score = metadata.get("contextAssertiveness")

        if isinstance(score, dict):
            return score

    return None


def main() -> int:
    failed = 0

    unit_errors = _validate_unit_multiturn()
    if unit_errors:
        failed += len(unit_errors)
        for error in unit_errors:
            print(f"FAIL unit: {error}", file=sys.stderr)
    else:
        print("OK unit multiturn assertividade")

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 1 if unit_errors else 0

    agent_id = _first_official_agent(token)
    session_id = _create_session(token, agent_id)

    _send_message(token, session_id, "me fale do produto 10080001", agent_id)
    _send_message(token, session_id, "agora estoque", agent_id)

    messages = _list_messages(token, session_id)
    assertiveness = _latest_assistant_assertiveness(messages)

    if not assertiveness:
        print(
            "FAIL API: contextAssertiveness ausente na última resposta do assistente",
            file=sys.stderr,
        )
        failed += 1
    elif float(assertiveness.get("score", 0)) < 50:
        print(f"WARN API: score baixo após follow-up: {assertiveness}", file=sys.stderr)
    else:
        flags = assertiveness.get("flags") or []
        print(f"OK API multiturn: score={assertiveness.get('score')} flags={flags}")

    admin_debug = (_send_message(token, session_id, "qual o estoque?", agent_id) or {}).get(
        "adminDebug"
    )
    if isinstance(admin_debug, dict) and admin_debug.get("contextAssertiveness"):
        print("OK API adminDebug expõe contextAssertiveness na resposta")
    elif admin_debug is None:
        print("SKIP API adminDebug (usuário sem permissão admin na resposta)")
    else:
        print(
            "WARN API: adminDebug sem contextAssertiveness (ver resolve_client_admin_debug)",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke HTTP — chips «Próximos passos» após consulta de produto.

Uso:
  PYTHONPATH=/app python scripts/smoke_follow_up_chips.py
  SMOKE_BASE_URL=http://localhost SMOKE_USER=rober SMOKE_PASSWORD=1234 python scripts/smoke_follow_up_chips.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)
from scripts.smoke_api_externa_helpers import validate_chip_action_id

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()

_EXPECTED_QUERIES = {
    "Ver estoque": "qual o estoque do produto {{productCode}}?",
    "Ver fornecedores": "liste os fornecedores do produto {{productCode}}",
    "Ver estrutura": "mostre a estrutura do produto {{productCode}}",
    "Ver vendas": "mostre o faturamento do produto {{productCode}}",
    "Onde é usado?": "onde o produto {{productCode}} é usado?",
}

_PRODUCT_CODE_SMOKE = "10080001"


def _fill_product_placeholder(query: str, product_code: str = _PRODUCT_CODE_SMOKE) -> str:
    return query.replace("{{productCode}}", product_code)

_ACTION_HINTS = {
    "Ver estoque": ("stock",),
    "Ver fornecedores": ("supplier", "fornecedor"),
    "Ver estrutura": ("structure", "estrutura"),
    "Ver vendas": ("sales", "billing", "faturamento", "venda"),
    "Onde é usado?": ("parent", "parents", "pai"),
}


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
        body={"title": "Smoke follow-up chips", "agentId": agent_id},
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


def _validate_unit_build() -> list[str]:
    errors: list[str] = []
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080001",
        answer="Informações do produto.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080001/analyser",
                    "humanizedSummary": {"titulo": "Informações completas do produto 10080001"},
                },
            }
        ],
        workspace_context={
            "actionsEnabled": True,
            "userActivatedAgent": True,
            "workingMemory": {"operationalFocus": {"productCode": "10080001"}},
        },
    )
    by_label = {item["label"]: item["query"] for item in suggestions}

    for label, expected in _EXPECTED_QUERIES.items():
        actual = by_label.get(label)
        if actual != expected:
            errors.append(f"unit build: {label!r} esperado {expected!r}, obteve {actual!r}")

    for item in suggestions:
        if "{product_code}" in item["query"]:
            errors.append(f"placeholder legado não convertido: {item}")
        if item["label"] in _EXPECTED_QUERIES and "{{productCode}}" not in item["query"]:
            errors.append(f"esperado {{{{productCode}}}} no chip: {item}")

    return errors


def _extract_follow_ups(messages: list[dict]) -> list[dict]:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue

        metadata = message.get("metadata") or {}
        suggestions = metadata.get("followUpSuggestions") or []

        if suggestions:
            return list(suggestions)

    return []


def _action_id_from_response(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        if call.get("name") != "execute_external_action":
            continue

        args = call.get("arguments") or {}
        action_id = str(args.get("actionId") or "").lower()

        if action_id:
            return action_id

    return ""


def main() -> int:
    failed = 0

    unit_errors = _validate_unit_build()
    if unit_errors:
        failed += len(unit_errors)
        for error in unit_errors:
            print(f"FAIL unit: {error}", file=sys.stderr)
    else:
        print("OK unit build follow-up queries")

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 1 if unit_errors else 0

    agent_id = _first_official_agent(token)
    session_id = _create_session(token, agent_id)

    bootstrap = _send_message(token, session_id, "me fale do produto 10080001", agent_id)
    messages = _list_messages(token, session_id)
    follow_ups = _extract_follow_ups(messages)

    if not follow_ups:
        print("FAIL API: followUpSuggestions ausente na resposta do produto", file=sys.stderr)
        failed += 1
    else:
        by_label = {item["label"]: item["query"] for item in follow_ups if isinstance(item, dict)}
        for label, expected in _EXPECTED_QUERIES.items():
            actual = by_label.get(label)
            if actual != expected:
                print(
                    f"FAIL API bootstrap: {label!r} esperado {expected!r}, obteve {actual!r}",
                    file=sys.stderr,
                )
                failed += 1
        if not failed:
            print(f"OK API bootstrap: {len(follow_ups)} chips com placeholder de produto")

    for label, query_template in _EXPECTED_QUERIES.items():
        query = _fill_product_placeholder(query_template)
        chip_session = _create_session(token, agent_id)
        _send_message(token, chip_session, "me fale do produto 10080001", agent_id)
        response = _send_message(token, chip_session, query, agent_id)
        action_id = _action_id_from_response(response)
        answer_lower = str(response.get("answer") or "").lower()
        hints = _ACTION_HINTS[label]

        ok_provider, provider_msg = validate_chip_action_id(
            label=label,
            action_id=action_id,
            query=query,
        )

        if provider_msg.startswith("SKIP"):
            print(provider_msg)
            continue

        if not ok_provider:
            print(provider_msg, file=sys.stderr)
            failed += 1
            continue

        if any(hint in action_id for hint in hints):
            print(provider_msg)
            continue

        if label == "Ver estoque" and not action_id and "estoque" in answer_lower:
            print("OK API chip Ver estoque: resposta direta (sem nova tool)")
            continue

        print(
            f"FAIL API chip {label!r}: actionId={action_id!r} (query={query!r})",
            file=sys.stderr,
        )
        failed += 1

    if bootstrap.get("answer") and "code:" in str(bootstrap.get("answer")).lower():
        print(
            "WARN bootstrap answer ainda parece formato técnico (ver presenter)",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

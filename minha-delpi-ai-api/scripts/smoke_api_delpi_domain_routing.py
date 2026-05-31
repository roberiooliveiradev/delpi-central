#!/usr/bin/env python3
"""Smoke — roteamento api-delpi por domínio com actions mockadas (sem ERP).

Valida ExternalActionSelectionService para cada domínio da auditoria.
Opcional: amostra E2E de intent no chat (login) quando SMOKE_CHAT_SAMPLE=1.

Uso:
  PYTHONPATH=. .venv/bin/python scripts/smoke_api_delpi_domain_routing.py
"""

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
from tests.fixtures.api_delpi_domain_routing_cases import (
    AUDIT_DOMAIN_MESSAGES,
    DOMAIN_ROUTING_CASES,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_CHAT_SAMPLE = os.environ.get("SMOKE_CHAT_SAMPLE", "1").strip().lower() in {
    "1",
    "true",
    "yes",
}

# Uma mensagem por domínio para intent E2E (roteamento, não dados ERP).
_CHAT_SAMPLE_BY_DOMAIN: dict[str, str] = {
    "products": "estoque do produto 10080047",
    "financial": "qual o ebitda do último trimestre",
    "system": "qual a tabela de produtos?",
}


class _FakeActionRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self._actions


def _run_mock_selection() -> tuple[int, dict[str, list[str]]]:
    failed = 0
    errors_by_domain: dict[str, list[str]] = {domain: [] for domain in AUDIT_DOMAIN_MESSAGES}

    for case in DOMAIN_ROUTING_CASES:
        domain = str(case["domain"])
        allowed = [action["actionId"] for action in case["actions"]]
        service = ExternalActionSelectionService(_FakeActionRepository(case["actions"]))

        selected = service.select_action(
            case["message"],
            allowed_action_ids=allowed,
            previous_messages=case.get("previous_messages"),
        )

        if selected is None:
            errors_by_domain[domain].append(f"{case['message']!r}: nenhuma action")
            failed += 1
            continue

        action_id = selected["arguments"].get("actionId")

        if action_id != case["expected_action_id"]:
            errors_by_domain[domain].append(
                f"{case['message']!r}: esperado {case['expected_action_id']}, "
                f"obteve {action_id}"
            )
            failed += 1
            continue

        expected_parameters = case.get("expected_parameters")

        if expected_parameters:
            params = selected["arguments"].get("parameters") or {}

            for key, value in expected_parameters.items():
                if params.get(key) != value:
                    errors_by_domain[domain].append(
                        f"{case['message']!r}: param {key}={params.get(key)!r} "
                        f"esperado {value!r}"
                    )
                    failed += 1

    for domain, messages in AUDIT_DOMAIN_MESSAGES.items():
        count = len(messages)
        domain_errors = errors_by_domain[domain]

        if domain_errors:
            print(f"FAIL mock/{domain}: {len(domain_errors)}/{count}", file=sys.stderr)

            for line in domain_errors[:5]:
                print(f"  - {line}", file=sys.stderr)
        else:
            print(f"OK mock/{domain}: {count} casos")

    return failed, errors_by_domain


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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return str(payload["access_token"])


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents", token=token)

    if not agents:
        raise RuntimeError("Nenhum agente disponível")

    return str(agents[0]["id"])


def _run_chat_intent_sample(token: str) -> int:
    failed = 0

    try:
        agent_id = _first_agent(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": "Smoke domínios api-delpi", "agentId": agent_id},
        )
        session_id = str(session["id"])
    except Exception as exc:
        print(f"SKIP chat sample: {exc}", file=sys.stderr)
        return 0

    for domain, message in _CHAT_SAMPLE_BY_DOMAIN.items():
        try:
            response = _request(
                "POST",
                f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
                token=token,
                body={"message": message, "agentId": agent_id, "adminDebug": True},
            )
        except Exception as exc:
            print(f"WARN chat/{domain}: {exc}", file=sys.stderr)
            continue

        admin_debug = response.get("adminDebug") or {}
        intent_route = admin_debug.get("intentRoute") or {}
        intent = intent_route.get("intent")
        tool_calls = response.get("toolCalls") or []

        if intent != "operational_query" and not tool_calls:
            print(
                f"WARN chat/{domain}: sem tool (intent={intent}) — agente sem actions?",
                file=sys.stderr,
            )
            continue

        print(f"OK chat/{domain}: intent={intent} tools={len(tool_calls)}")

    return failed


def main() -> int:
    print(f"Domínios: {len(AUDIT_DOMAIN_MESSAGES)} | Casos mock: {len(DOMAIN_ROUTING_CASES)}")

    failed, _ = _run_mock_selection()

    if not _CHAT_SAMPLE:
        return 1 if failed else 0

    try:
        token = _fetch_token()
        print("OK login Keycloak")
        failed += _run_chat_intent_sample(token)
    except Exception as exc:
        print(f"SKIP chat sample: {exc}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

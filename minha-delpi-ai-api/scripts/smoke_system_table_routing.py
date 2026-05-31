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

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

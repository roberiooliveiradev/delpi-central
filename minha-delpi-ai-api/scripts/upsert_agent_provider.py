#!/usr/bin/env python3
"""Habilita ou desabilita provider OpenAPI em um agente via API (sem migration de dados).

Usa `PUT /chat/agents/{agentId}/providers` — ver docs/api/04-actions-openapi.md.

Exemplos:
  # Agente oficial: só api-externa (homologação local)
  PYTHONPATH=. python scripts/upsert_agent_provider.py \\
    --provider api-externa --enabled true \\
    --provider api-delpi --enabled false

  # Produção: habilitar api-delpi para faturamento/vendas
  PYTHONPATH=. python scripts/upsert_agent_provider.py \\
    --provider api-delpi --enabled true

Variáveis: SMOKE_BASE_URL, SMOKE_USER, SMOKE_PASSWORD, SMOKE_REALM, SMOKE_CLIENT_ID.
Se o banco foi migrado com revision removida `p8q9r0s1t3`, alinhe o Alembic:
  flask db stamp o7p8q9r0s1t2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
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


def _upsert_provider(
    token: str,
    agent_id: str,
    *,
    provider_key: str,
    enabled: bool,
) -> None:
    body = {
        "providerKey": provider_key,
        "enabled": enabled,
        "allowRead": True,
        "allowWrite": False,
        "allowAdmin": False,
        "requiresConfirmationForWrite": True,
    }
    _request(
        "PUT",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers",
        token=token,
        body=body,
    )
    state = "habilitado" if enabled else "desabilitado"
    print(f"OK {provider_key} {state} no agente {agent_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent-id",
        help="UUID do agente (padrão: primeiro agente system habilitado)",
    )
    parser.add_argument(
        "--provider",
        action="append",
        dest="providers",
        metavar="KEY",
        required=True,
        help="provider_key (ex.: api-externa, api-delpi)",
    )
    parser.add_argument(
        "--enabled",
        action="append",
        dest="enabled_flags",
        metavar="BOOL",
        required=True,
        help="true/false para cada --provider (mesma ordem)",
    )
    args = parser.parse_args()

    if len(args.providers) != len(args.enabled_flags):
        print("FAIL: informe --enabled para cada --provider", file=sys.stderr)
        return 1

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = args.agent_id or _first_official_agent(token)

    for provider_key, enabled_raw in zip(args.providers, args.enabled_flags, strict=True):
        enabled = str(enabled_raw).lower() in ("1", "true", "yes", "on")
        try:
            _upsert_provider(
                token,
                agent_id,
                provider_key=provider_key.strip(),
                enabled=enabled,
            )
        except Exception as exc:
            print(f"FAIL {provider_key}: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

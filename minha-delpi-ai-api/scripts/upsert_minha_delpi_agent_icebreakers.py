#!/usr/bin/env python3
"""Atualiza quebra-gelos do Agente Minha DELPI via API (sem migration).

Fluxo:
  GET  /chat/agents
  GET  /chat/agents/{id}
  PATCH /chat/agents/{id}  → metadata.icebreakers
  POST /chat/agents/{id}/publish

Cada item em `metadata.icebreakers`:
  - string legada: só a pergunta com `{{productCode}}`, etc.
  - objeto: `{ template, label, hint, fields[] }` — card configurável na home

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. python3 scripts/upsert_minha_delpi_agent_icebreakers.py
"""

from __future__ import annotations

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
_AGENT_ID = os.environ.get("MINHA_DELPI_AGENT_ID", "").strip()
_AGENT_NAME = os.environ.get("MINHA_DELPI_AGENT_NAME", "Agente Minha DELPI").strip()

_PRODUCT_FIELD = {
    "id": "productCode",
    "label": "Código do produto",
    "fieldType": "productCode",
    "required": True,
}

DEFAULT_AGENT_ICEBREAKERS: list[dict[str, object]] = [
    {
        "template": "me fale do produto {{productCode}}",
        "label": "Consultar produto",
        "hint": "Cadastro, estoque e visão geral",
        "fields": [_PRODUCT_FIELD],
    },
    {
        "template": "qual o status fabril hoje do produto {{productCode}}?",
        "label": "Status fabril",
        "hint": "Estrutura, MPs, produção e expedição",
        "fields": [_PRODUCT_FIELD],
    },
    {
        "template": "quais MPs exclusivas tem o produto {{productCode}}?",
        "label": "MPs exclusivas",
        "hint": "Matérias-primas usadas só neste PA",
        "fields": [_PRODUCT_FIELD],
    },
    {
        "template": "análise de preço da matéria-prima {{productCode}}",
        "label": "Preço da MP",
        "hint": "Fornecedor, ICMS, orçamento e variação",
        "fields": [
            {
                "id": "productCode",
                "label": "Código da matéria-prima",
                "fieldType": "productCode",
                "required": True,
            }
        ],
    },
    {
        "template": "quais materiais mais impactam o custo do PA {{productCode}}?",
        "label": "Impacto de custo",
        "hint": "Ranking Pareto das MPs na BOM",
        "fields": [
            {
                "id": "productCode",
                "label": "Código do PA",
                "fieldType": "productCode",
                "required": True,
            }
        ],
    },
    {
        "template": "qual o estoque do produto {{productCode}}?",
        "label": "Ver estoque",
        "hint": "Saldo por filial e local",
        "fields": [_PRODUCT_FIELD],
    },
    {
        "template": "o que você pode fazer?",
        "label": "Capacidades",
        "hint": "Ferramentas, dados e limites do agente",
        "fields": [],
    },
]


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} → HTTP {exc.code}: {detail}") from exc


def _token() -> str:
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
        raise RuntimeError("Token ausente na resposta do Keycloak")

    return str(token)


def _resolve_agent_id(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID

    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents", token=token)

    if not isinstance(agents, list):
        raise RuntimeError("Resposta inesperada em GET /agents")

    for agent in agents:
        name = str(agent.get("name") or "").strip()
        if name == _AGENT_NAME and agent.get("enabled"):
            return str(agent["id"])

    for agent in agents:
        name = str(agent.get("name") or "").strip().lower()
        if "minha delpi" in name and agent.get("enabled"):
            return str(agent["id"])

    raise RuntimeError(f"Agente «{_AGENT_NAME}» não encontrado")


def main() -> int:
    token = _token()
    agent_id = _resolve_agent_id(token)
    base = f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}"

    agent = _request("GET", base, token=token)
    metadata = dict(agent.get("metadata") or {})
    before = list(metadata.get("icebreakers") or [])

    metadata["icebreakers"] = [dict(item) for item in DEFAULT_AGENT_ICEBREAKERS]

    updated = _request("PATCH", base, token=token, body={"metadata": metadata})
    published = _request("POST", f"{base}/publish", token=token)

    after = list((published.get("metadata") or updated.get("metadata") or {}).get("icebreakers") or [])

    print(f"Agente: {agent.get('name')} ({agent_id})")
    print(f"Quebra-gelos antes ({len(before)}): {json.dumps(before, ensure_ascii=False)}")
    print(f"Quebra-gelos depois ({len(after)}): {json.dumps(after, ensure_ascii=False)}")

    if after != metadata["icebreakers"]:
        print("ERRO: icebreakers publicados diferem do esperado.", file=sys.stderr)
        return 1

    print("OK — icebreakers configuráveis (label/hint/fields) atualizados e publicados via API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

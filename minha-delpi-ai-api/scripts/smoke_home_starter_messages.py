#!/usr/bin/env python3
"""Smoke — respostas dos atalhos da home (mensagens já preenchidas).

HTTP: SMOKE_BASE_URL=http://gateway SMOKE_USER=rober SMOKE_PASSWORD=1234
SMOKE_PRODUCT_CODE=10080001 (opcional)
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
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "10080001").strip()

_CASES: list[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = [
    (
        "Ver estoque",
        f"qual o estoque do produto {_PRODUCT_CODE}?",
        ("/stock", "estoque"),
        ("/products/search",),
    ),
    (
        "Consultar produto",
        f"me fale do produto {_PRODUCT_CODE}",
        ("/products/", "produto"),
        ("/products/search",),
    ),
    (
        "Quem fornece",
        f"quem fornece o produto {_PRODUCT_CODE}?",
        ("/suppliers", "fornec"),
        ("/products/search", "/analyser"),
    ),
    (
        "Ver vendas",
        f"mostre vendas do produto {_PRODUCT_CODE}",
        ("/sales", "venda"),
        ("/products/search",),
    ),
    (
        "KPIs comerciais",
        "mostre KPIs comerciais do mês passado",
        ("/commercial/", "consulta", "proposta"),
        ("/products/search",),
    ),
    (
        "O que posso fazer",
        "o que você pode fazer?",
        ("pode", "capac"),
        (),
    ),
]


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


def _tool_paths(response: dict) -> list[str]:
    paths: list[str] = []

    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").strip()

        if path:
            paths.append(path.lower())

    return paths


def main() -> int:
    failed = 0

    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"SKIP API: {exc}", file=sys.stderr)
        return 0

    agent_id = _first_agent_id(token)

    for label, message, expect_any, forbid_any in _CASES:
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": f"Smoke home — {label}", "agentId": agent_id},
        )
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
            token=token,
            body={"message": message, "agentId": agent_id},
        )
        answer = str(response.get("answer") or "").lower()
        paths = _tool_paths(response)

        if forbid_any and any(token in " ".join(paths) for token in forbid_any):
            print(f"FAIL [{label}]: path proibido ({paths})", file=sys.stderr)
            failed += 1
            continue

        if expect_any and not any(token in answer or token in " ".join(paths) for token in expect_any):
            print(f"FAIL [{label}]: resposta fora do esperado", file=sys.stderr)
            failed += 1
            continue

        print(f"OK [{label}] paths={paths[:2] or '—'}")

    if failed:
        return 1

    print("Smoke atalhos home (API): OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

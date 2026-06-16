#!/usr/bin/env python3
"""Smoke — «mostre vendas do produto» usa /sales (api-delpi), não /stock."""

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

_SALES_MESSAGE = os.environ.get(
    "SMOKE_SALES_MESSAGE",
    "mostre vendas do produto 10080001",
).strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "10080001").strip()


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
        if agent.get("enabled") and agent.get("visibility") == "system":
            return str(agent["id"])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _ensure_api_delpi_enabled(token: str, agent_id: str) -> None:
    """Vendas do produto existem em api-delpi; api-externa não expõe /products/{code}/sales."""
    providers = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers",
        token=token,
    )
    items = providers if isinstance(providers, list) else providers.get("items", [])
    delpi_enabled = any(
        isinstance(item, dict)
        and str(item.get("providerKey") or item.get("key") or "") == "api-delpi"
        and item.get("enabled")
        for item in items
    )
    if delpi_enabled:
        print("OK API: provider api-delpi já habilitado")
        return

    _request(
        "PUT",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers",
        token=token,
        body={
            "providerKey": "api-delpi",
            "enabled": True,
            "allowRead": True,
            "allowWrite": False,
            "allowAdmin": False,
            "requiresConfirmationForWrite": True,
        },
    )
    print("OK API: provider api-delpi habilitado para smoke de vendas")


def main() -> int:
    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntent,
        ChatProductQueryIntentService,
    )

    intent = ChatProductQueryIntentService.detect(_SALES_MESSAGE)
    if intent != ChatProductQueryIntent.SALES:
        print(f"FAIL unit: intent={intent!r}, esperado SALES", file=sys.stderr)
        return 1
    print("OK unit: intent SALES detectada")

    try:
        token = _fetch_token()
        print("OK login Keycloak")
    except Exception as exc:
        print(f"SKIP API (sem token): {exc}", file=sys.stderr)
        return 0

    agent_id = _first_agent_id(token)
    _ensure_api_delpi_enabled(token, agent_id)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke vendas produto", "agentId": agent_id},
    )
    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session['id']}/messages",
        token=token,
        body={"message": _SALES_MESSAGE, "agentId": agent_id},
    )

    tool_calls = response.get("toolCalls") or []
    admin_debug = response.get("adminDebug") or {}
    intent_route = admin_debug.get("intentRoute") or {}
    sub_intent = str(intent_route.get("subIntent") or "")

    sales_path = False
    stock_path = False
    action_id = ""

    for call in tool_calls:
        if call.get("name") != "execute_external_action":
            continue
        args = call.get("arguments") or {}
        action_id = str(args.get("actionId") or "")
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()
        if f"/products/{_PRODUCT_CODE}/sales" in path or path.rstrip("/").endswith("/sales"):
            sales_path = True
        if "/stock" in path:
            stock_path = True

    if stock_path and not sales_path:
        print(
            f"FAIL API: roteou estoque ({action_id}) em vez de vendas",
            file=sys.stderr,
        )
        return 1

    if not sales_path:
        print(f"FAIL API: toolCalls sem /sales ({len(tool_calls)} calls)", file=sys.stderr)
        return 1

    print(f"OK API: consulta vendas ({action_id or 'path /sales'})")

    if sub_intent == "sales_lookup":
        print("OK API: subIntent sales_lookup")
    elif sub_intent:
        print(f"WARN API: subIntent={sub_intent!r}", file=sys.stderr)

    title = ""
    for call in tool_calls:
        meta = (call.get("metadata") or {})
        summary = meta.get("humanizedSummary") or {}
        title = str(summary.get("titulo") or "").lower()
        if title:
            break

    if "estoque" in title and "venda" not in title:
        print(f"FAIL API: título humanizado={title!r}", file=sys.stderr)
        return 1

    if title:
        print(f"OK API: título humanizado coerente ({title[:60]})")

    selected = admin_debug.get("tooling", {}).get("selectedExternalAction") or {}
    selected_id = str(selected.get("actionId") or "")
    if selected_id and "stock" in selected_id.lower() and "sales" not in selected_id.lower():
        print(f"FAIL API: selectedExternalAction={selected_id}", file=sys.stderr)
        return 1

    if selected_id:
        print(f"OK API: selectedExternalAction={selected_id}")

    if not ExternalActionProductRouteCatalogService.is_product_sales_summary_path(
        f"/products/{_PRODUCT_CODE}/sales"
    ):
        print("FAIL unit: helper is_product_sales_summary_path", file=sys.stderr)
        return 1

    print("Smoke vendas produto: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

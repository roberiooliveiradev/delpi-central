#!/usr/bin/env python3
"""Smoke — follow-up «notas fiscais de saída» usa /outbound-invoice-items (api-delpi).

Requer PYTHONPATH=/app. Ex.: PYTHONPATH=/app SMOKE_BASE_URL=http://gateway python scripts/smoke_outbound_invoice_routing.py
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

_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90260145").strip()
_SALES_MESSAGE = f"mostre vendas do produto {_PRODUCT_CODE}"
_NF_MESSAGE = os.environ.get("SMOKE_NF_MESSAGE", "notas fiscais de saída").strip()


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


def _ensure_api_delpi_enabled(token: str, agent_id: str) -> None:
    providers = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/agents/{agent_id}/providers",
        token=token,
    )
    items = providers if isinstance(providers, list) else providers.get("items", [])
    if any(
        isinstance(item, dict)
        and str(item.get("providerKey") or item.get("key") or "") == "api-delpi"
        and item.get("enabled")
        for item in items
    ):
        print("OK API: provider api-delpi habilitado")
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
    print("OK API: provider api-delpi habilitado para smoke")


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


def _tool_paths(response: dict) -> list[str]:
    paths: list[str] = []
    for call in response.get("toolCalls") or []:
        if call.get("name") != "execute_external_action":
            continue
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "").lower()
        if path:
            paths.append(path)
    return paths


def _presentation_type(response: dict) -> str | None:
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        presentation = meta.get("presentation")
        if isinstance(presentation, dict) and presentation.get("type"):
            return str(presentation["type"])
    return None


def main() -> int:
    from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
    from app.domain.services.chat_intent_router_service import ChatIntentRouterService
    from app.domain.services.chat_route_context_service import ChatRouteContextService

    history = [
        {"role": "user", "content": _SALES_MESSAGE},
        {
            "role": "assistant",
            "content": "Resumo de vendas",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": f"/products/{_PRODUCT_CODE}/sales",
                        },
                    }
                ]
            },
        },
    ]

    if not ChatRouteContextService.segment_from_message(_NF_MESSAGE):
        print("FAIL unit: segment_from_message vazio", file=sys.stderr)
        return 1
    print(f"OK unit: segment={ChatRouteContextService.segment_from_message(_NF_MESSAGE)!r}")

    if not ChatFollowUpIntentService.is_operational_follow_up(_NF_MESSAGE):
        print("FAIL unit: não detectou follow-up operacional", file=sys.stderr)
        return 1
    print("OK unit: follow-up operacional")

    route = ChatIntentRouterService.classify(
        _NF_MESSAGE,
        previous_messages=history,
        allowed_action_ids=["action-1"],
    )
    if route.intent != "operational_query":
        print(f"FAIL unit: intent={route.intent!r}", file=sys.stderr)
        return 1
    print(f"OK unit: intent operacional (sub={route.sub_intent!r})")

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
        body={"title": "Smoke NF saída", "agentId": agent_id},
    )
    session_id = str(session["id"])

    sales_resp = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": _SALES_MESSAGE, "agentId": agent_id},
    )
    sales_paths = _tool_paths(sales_resp)
    if not any(f"/products/{_PRODUCT_CODE}/sales" in path for path in sales_paths):
        print(f"FAIL API: vendas sem /sales ({sales_paths})", file=sys.stderr)
        return 1
    print("OK API: vendas via /sales")

    nf_resp = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": _NF_MESSAGE, "agentId": agent_id},
    )
    nf_paths = _tool_paths(nf_resp)
    if not any("outbound-invoice" in path for path in nf_paths):
        print(f"FAIL API: NF sem outbound-invoice ({nf_paths})", file=sys.stderr)
        return 1
    print(f"OK API: notas de saída via outbound-invoice ({nf_paths[0]})")

    presentation = _presentation_type(nf_resp)
    if presentation != "table":
        print(f"WARN API: presentation.type={presentation!r} (esperado table)", file=sys.stderr)
    else:
        print("OK API: apresentação em tabela")

    admin_debug = nf_resp.get("adminDebug") or {}
    stages = admin_debug.get("pipelineStages") or []
    if "agentic" in stages and "tools" not in stages:
        print(f"FAIL API: pipeline sem tools ({stages})", file=sys.stderr)
        return 1
    print("OK API: pipeline com tools")

    print("Smoke notas fiscais de saída: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

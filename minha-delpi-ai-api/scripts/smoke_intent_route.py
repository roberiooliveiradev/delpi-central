#!/usr/bin/env python3
"""Smoke — intentRoute no adminDebug e estágio intent:* (Playbook 01)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from app.domain.services.chat_intent_router_service import ChatIntentRouterService

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


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def main() -> int:
    failed = 0

    route = ChatIntentRouterService.classify("obrigado!")
    if route.intent != "small_talk":
        print(f"FAIL unit: classify obrigado -> {route.intent}", file=sys.stderr)
        failed += 1
    else:
        print("OK unit: classify small_talk")

    doc_route = ChatIntentRouterService.classify(
        "o que esta escrito no arquivo?",
        attachment_ids=["att-smoke"],
    )
    if doc_route.intent not in {"attachment_document", "attachment_task"}:
        print(
            f"FAIL unit: classify anexo -> {doc_route.intent}",
            file=sys.stderr,
        )
        failed += 1
    else:
        print(f"OK unit: classify anexo intent={doc_route.intent}")

    try:
        token = _fetch_token()
        agent_id = _first_agent(token)
        session = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
            token=token,
            body={"title": "Smoke intent route", "agentId": agent_id},
        )
        session_id = str(session["id"])
        response = _request(
            "POST",
            f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
            token=token,
            body={"message": "obrigado!", "agentId": agent_id},
        )
    except Exception as exc:
        print(f"SKIP API: {exc}", file=sys.stderr)
        return 1 if failed else 0

    admin_debug = response.get("adminDebug") or {}
    intent_route = admin_debug.get("intentRoute") or {}
    stages = ((admin_debug.get("intelligence") or {}).get("pipeline") or {}).get("stages") or []

    if intent_route.get("intent") != "small_talk":
        print(f"FAIL API: intentRoute={intent_route}", file=sys.stderr)
        failed += 1
    else:
        print(f"OK API: intentRoute intent={intent_route.get('intent')}")

    if not any(str(stage).startswith("intent:") for stage in stages):
        print(f"FAIL API: stages sem intent:* -> {stages}", file=sys.stderr)
        failed += 1
    else:
        print(f"OK API: pipeline stages tail={stages[-3:]}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

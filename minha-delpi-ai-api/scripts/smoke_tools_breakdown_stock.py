#!/usr/bin/env python3
"""Smoke — toolsBreakdown no turno de estoque (latência toolsMs).

Uso:
  SMOKE_PRODUCT_CODE=10090016 python3 scripts/smoke_tools_breakdown_stock.py

Critério E1.S2: nomear o span de toolsBreakdown com maior fatia de toolsMs
(e extras wave*HttpMs / wave*PresentationMs).
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
_CHAT_PREFIX = os.environ.get(
    "SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat"
).strip()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10090016").strip()

_SPAN_KEYS = (
    "selectionMs",
    "wave1Ms",
    "criticMs",
    "wave2Ms",
    "assembleMs",
    "agenticExtendMs",
    "finalizeAfterToolsMs",
)
_EXTRA_KEYS = (
    "wave1HttpMs",
    "wave1PresentationMs",
    "wave2HttpMs",
    "wave2PresentationMs",
)


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 300,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=timeout) as response:
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
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=10", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível")


def main() -> int:
    try:
        token = _fetch_token()
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    agent_id = _first_agent(token)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "context": "geral"},
    )
    session_id = str(session["id"])
    message = f"estoque do produto {_PRODUCT}"
    print(f"OK session={session_id} msg={message!r}", flush=True)

    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
        timeout=360,
    )
    intelligence = (response.get("metadata") or {}).get("intelligence") or {}
    if not intelligence:
        intelligence = (response.get("adminDebug") or {}).get("intelligence") or {}
    if not intelligence:
        intelligence = response.get("intelligence") or {}
    timings = intelligence.get("timings") or {}
    breakdown = timings.get("toolsBreakdown") or {}
    tools_ms = int(timings.get("toolsMs") or 0)

    print("timings=", json.dumps(timings, ensure_ascii=False, indent=2))

    stock_ok = False
    sales_ok = False
    for call in response.get("toolCalls") or []:
        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")
        print(
            "tool=",
            json.dumps(
                {
                    "path": meta.get("path"),
                    "durationMs": meta.get("durationMs"),
                    "presentationMs": meta.get("presentationMs"),
                    "selected": (meta.get("presentationDecision") or {}).get("selected"),
                    "hasChart": bool(meta.get("chartPresentation")),
                },
                ensure_ascii=False,
            ),
        )
        if "/stock" in path.lower() and meta.get("ok"):
            stock_ok = True
            if meta.get("chartPresentation"):
                print("FAIL chartPresentation presente com chartPolicy skip", file=sys.stderr)
                return 3
            selected = str((meta.get("presentationDecision") or {}).get("selected") or "")
            if selected and selected != "table":
                print(f"WARN stock selected={selected!r} (esperado table no Automático)")
            role = str(meta.get("compositionRole") or "")
            if role and role != "primary":
                print(f"FAIL stock compositionRole={role!r}", file=sys.stderr)
                return 5
        if "/sales" in path.lower() and meta.get("ok"):
            sales_ok = True
            role = str(meta.get("compositionRole") or "")
            if role and role != "enrichment":
                print(f"FAIL sales compositionRole={role!r}", file=sys.stderr)
                return 6

    answer = str(response.get("answer") or "")
    print("answer_preview=", answer[:240])

    if not stock_ok:
        print("FAIL sem toolCall de estoque", file=sys.stderr)
        return 4

    if not sales_ok:
        print("WARN critic sales ausente (estoque pode não ter zero_value)")

    if not breakdown:
        print("FAIL toolsBreakdown ausente", file=sys.stderr)
        return 2

    hot_key, hot_ms = max(
        ((key, int(breakdown.get(key) or 0)) for key in _SPAN_KEYS),
        key=lambda item: item[1],
    )
    pct = (100.0 * hot_ms / tools_ms) if tools_ms else 0.0
    print(f"hot_span={hot_key}={hot_ms} ({pct:.1f}% of toolsMs={tools_ms})")

    extras = {
        key: breakdown.get(key)
        for key in _EXTRA_KEYS
        if breakdown.get(key) is not None
    }
    selection_breakdown = breakdown.get("selectionBreakdown")
    print("extras=", json.dumps(extras, ensure_ascii=False))
    if selection_breakdown:
        print(
            "selectionBreakdown=",
            json.dumps(selection_breakdown, ensure_ascii=False),
        )

    # Pós-E3 (ago/2026): wave1HttpMs caiu (NOLOCK+cache+query única).
    # Span dominante típico passou a selectionMs (~50%+ de toolsMs).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

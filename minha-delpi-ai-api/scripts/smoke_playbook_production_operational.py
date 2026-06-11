#!/usr/bin/env python3
"""Smoke E2E — Playbook 15 Fase 1 (consumo, compras, perdas, programação)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_API_PREFIX = os.environ.get("SMOKE_API_PREFIX", "/apps/api-delpi").strip()
_MAX_LATENCY_S = float(os.environ.get("SMOKE_MAX_LATENCY_SECONDS", "120"))
_PAUSE_S = float(os.environ.get("SMOKE_PAUSE_SECONDS", "2"))


def _request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=300) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


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
        raise RuntimeError("Token ausente")

    return str(token)


def _agent_id(token: str) -> str:
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    raise RuntimeError("Nenhum agente habilitado")


def _session(token: str, agent_id: str, title: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": title, "agentId": agent_id},
    )
    return str(payload["id"])


def _send(token: str, session_id: str, agent_id: str, message: str) -> tuple[dict, float]:
    started = time.monotonic()
    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )
    return response, time.monotonic() - started


def _action_info(response: dict) -> tuple[str, str, bool | None, dict | None]:
    for call in response.get("toolCalls") or []:
        name = str(call.get("name") or "")

        if name == "execute_external_action":
            meta = call.get("metadata") or {}
            path = str(meta.get("path") or "")
            operation_id = str(meta.get("operationId") or "")
            return path, operation_id, meta.get("ok"), call.get("arguments")

        if name == "execute_sql_query" or "sql" in name.lower():
            return "/data/sql", "execute_readonly_sql", None, call.get("arguments")

    return "", "", None, None


def _api_get(token: str, path: str) -> tuple[dict, float]:
    started = time.monotonic()
    payload = _request("GET", f"{_BASE_URL}{_API_PREFIX}{path}", token=token)
    return payload, time.monotonic() - started


def main() -> int:
    token = _token()
    agent_id = _agent_id(token)
    failed = 0

    api_checks: list[tuple[str, str]] = [
        ("API R01 consumption", "/production/consumption/top-items?limit=3"),
        ("API R04 purchases", "/purchases/top-products?limit=3"),
        ("API R07 losses top", "/production/losses/top-materials?limit=3"),
        ("API R06 losses records", "/production/losses/records?limit=3"),
        ("API R08 schedule", "/production/schedule/today?limit=3"),
    ]

    print("=== api-delpi direct ===")
    for title, path in api_checks:
        try:
            payload, elapsed = _api_get(token, path)
            success = bool(payload.get("success"))
            items = ((payload.get("data") or {}).get("items") or [])
            operation_id = ((payload.get("meta") or {}).get("operationId") or "")
            status = "OK" if success else "FAIL"
            print(
                f"{status} {title} — op={operation_id} items={len(items)} "
                f"latency={elapsed:.1f}s"
            )
            if not success:
                failed += 1
                print(f"    payload={json.dumps(payload, ensure_ascii=False)[:400]}", file=sys.stderr)
        except Exception as exc:
            failed += 1
            print(f"FAIL {title} — {exc}", file=sys.stderr)

    chat_scenarios: list[tuple[str, str, str, str | None]] = [
        (
            "S1 consumption",
            "Itens mais consumidos mês passado filial 01 top 10",
            "/production/consumption/top-items",
            "get_production_consumption_top_items",
        ),
        (
            "S2 purchases",
            "Produtos mais comprados março 2026",
            "/purchases/top-products",
            "get_purchases_top_products",
        ),
        (
            "S3 losses top",
            "Refugos de matéria-prima março filial 02 top 10",
            "/production/losses/top-materials",
            "get_production_losses_top_materials",
        ),
        (
            "S4 schedule today",
            "Quais produtos serão produzidos hoje?",
            "/production/schedule/today",
            "get_production_schedule_today",
        ),
    ]

    print("\n=== chat E2E ===")
    for title, message, expected_fragment, expected_operation in chat_scenarios:
        time.sleep(_PAUSE_S)
        session_id = _session(token, agent_id, title)
        response, elapsed = _send(token, session_id, agent_id, message)
        path, operation_id, ok, _arguments = _action_info(response)
        answer = str(response.get("answer") or response.get("content") or "")[:240]

        hit_path = expected_fragment in path
        hit_op = expected_operation in operation_id or expected_fragment in path
        no_sql = "/data/sql" not in path
        success = hit_path and hit_op and no_sql and elapsed <= _MAX_LATENCY_S

        if success:
            print(
                f"OK  {title} — path={path} op={operation_id} ok={ok} "
                f"latency={elapsed:.1f}s"
            )
            print(f"    answer={answer!r}")
            continue

        failed += 1
        print(f"FAIL {title}", file=sys.stderr)
        print(
            f"    path={path!r} op={operation_id!r} expected~={expected_fragment!r}",
            file=sys.stderr,
        )
        print(f"    ok={ok} no_sql={no_sql} latency={elapsed:.1f}s answer={answer!r}", file=sys.stderr)
        print(
            f"    toolCalls={json.dumps(response.get('toolCalls') or [], ensure_ascii=False)[:800]}",
            file=sys.stderr,
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

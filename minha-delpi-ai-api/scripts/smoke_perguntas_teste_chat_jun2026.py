#!/usr/bin/env python3
"""Smoke E2E — perguntas de docs/testing/perguntas-teste-chat-jun2026.md."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_STOCK = os.environ.get("SMOKE_STOCK_CODE", "10080022").strip()
_FABRIL = os.environ.get("SMOKE_PRODUCT_CODE", "90269002").strip()
_MP = os.environ.get("SMOKE_MP_CODE", "10080001").strip()
_PA = os.environ.get("SMOKE_PA_CODE", "90261255").strip()
_MAX_LATENCY_S = float(os.environ.get("SMOKE_MAX_LATENCY_SECONDS", "45"))


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

    return str(items[0]["id"])


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


def _action_path(response: dict) -> str:
    for call in response.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        meta = call.get("metadata") or {}

        if meta.get("ok"):
            return str(meta.get("path") or "")

    for call in response.get("toolCalls") or []:
        if str(call.get("name") or "") != "execute_external_action":
            continue

        meta = call.get("metadata") or {}
        path = str(meta.get("path") or "")

        if path:
            return path

    return ""


def _pending_kind(token: str, session_id: str) -> str:
    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages if isinstance(messages, list) else messages.get("items", [])

    for item in reversed(items):
        if str(item.get("role") or "") != "assistant":
            continue

        pending = (item.get("metadata") or {}).get("activePending")

        if isinstance(pending, dict):
            return str(pending.get("kind") or "")

    return ""


def _llm_improvised(response: dict) -> bool:
    admin = response.get("adminDebug") or {}
    intelligence = admin.get("intelligence") or {}
    pipeline = intelligence.get("pipeline") or {}
    stages = list(pipeline.get("stages") or [])
    content = str(response.get("content") or response.get("answer") or "").lower()

    if any(stage in {"llm_synthesis", "agentic_loop", "llm_general"} for stage in stages):
        return True

    if "operational_parameter" in stages:
        return False

    if _action_path(response):
        return False

    markers = (
        "nao tenho acesso",
        "não tenho acesso",
        "infelizmente nao consigo",
        "infelizmente não consigo",
    )

    return any(marker in content for marker in markers)


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK  {label}" + (f" — {detail}" if detail else ""))
        return

    print(f"FAIL {label}" + (f" — {detail}" if detail else ""), file=sys.stderr)
    raise AssertionError(label)


def _path_matches(path: str, expected: str | tuple[str, ...]) -> bool:
    if isinstance(expected, tuple):
        return any(fragment in path for fragment in expected)

    return expected in path


def main() -> int:
    failed = 0
    token = _token()
    agent_id = _agent_id(token)

    single_turn: list[tuple[str, str, str | tuple[str, ...], bool]] = [
        ("R1 estoque", f"estoque do produto {_STOCK}", "/stock", True),
        ("R2 status fabril", f"status fabril do produto {_FABRIL} hoje", "/factory-status", True),
        ("R3 análise MP", f"análise de preço da matéria-prima {_MP}", "/raw-material-price-intelligence", True),
        ("R4 simulador PA", f"quais materiais mais impactam o custo do PA {_PA}?", "/cost-impact-simulation", True),
        ("R5 preço venda", f"qual o preço de venda do produto {_MP}?", "/pricing", True),
        ("F2 produção", f"situação de produção do {_FABRIL} hoje", "/production-status", True),
        ("F3 expedição", f"inspeção final expedição produto {_FABRIL} hoje", "/shipping-status", True),
        ("F4 exclusividade", f"quais matérias-primas exclusivas existem na estrutura do produto {_FABRIL}?", "/structure/exclusivity", True),
        ("MP1 intelligence", f"Análise de preço da matéria-prima {_MP}", "/raw-material-price-intelligence", True),
        ("MP2 ICMS", f"Última compra e ICMS do produto {_MP}", ("/last-purchase", "/raw-material-price-intelligence"), True),
        ("MP3 orçamento", f"Histórico de orçamento de compra do produto {_MP}", "/purchase-budget-history", True),
        ("MP4 histórico preço", f"Histórico de preço de compra do {_MP}", "/purchase-price-history", True),
        ("MP6 simulação +10%", f"Simule aumento de 10% nos materiais do produto {_PA}", "/cost-impact-simulation", True),
        ("MP8 pricing", f"Qual o preço de venda do produto {_MP}?", "/pricing", True),
        ("MP9 purchases", f"últimas compras do produto {_MP}", "/purchases", True),
        ("D1 não intelligence", f"Qual o preço de venda do produto {_MP}?", "/raw-material-price-intelligence", False),
    ]

    for title, message, expected_fragment, expect_match in single_turn:
        try:
            session_id = _session(token, agent_id, title)
            response, elapsed = _send(token, session_id, agent_id, message)
            path = _action_path(response)

            if elapsed > _MAX_LATENCY_S:
                _check(title, False, f"latência {elapsed:.1f}s")

            if _llm_improvised(response):
                _check(title, False, f"improvisação LLM path={path or '?'}")

            if expect_match:
                _check(title, _path_matches(path, expected_fragment), f"path={path or '?'} elapsed={elapsed:.1f}s")
            else:
                if isinstance(expected_fragment, tuple):
                    _check(title, not any(fragment in path for fragment in expected_fragment), f"path={path or '?'}")
                else:
                    _check(title, expected_fragment not in path, f"path={path or '?'}")
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL {title} — {exc}", file=sys.stderr)
            failed += 1

    try:
        session_id = _session(token, agent_id, "F5 pending date")
        _send(token, session_id, agent_id, f"status fabril do produto {_FABRIL}")
        pending = _pending_kind(token, session_id)
        _check(
            "F5 pede data",
            pending in {"missing_date", "missing_period"} or "data" in pending or "periodo" in pending,
            f"pending={pending or '?'}",
        )
        follow, elapsed = _send(token, session_id, agent_id, "hoje")
        path = _action_path(follow)
        _check(
            "F6 continuação hoje",
            "/factory-status" in path and not _llm_improvised(follow),
            f"path={path or '?'} elapsed={elapsed:.1f}s",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL F5/F6 — {exc}", file=sys.stderr)
        failed += 1

    try:
        session_id = _session(token, agent_id, "MP10 sessão ativa")
        _send(token, session_id, agent_id, "análise de preço MP")
        follow, elapsed = _send(token, session_id, agent_id, _MP)
        path = _action_path(follow)
        _check(
            "MP10 código isolado",
            "/raw-material-price-intelligence" in path,
            f"path={path or '?'} elapsed={elapsed:.1f}s",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL MP10 — {exc}", file=sys.stderr)
        failed += 1

    try:
        session_id = _session(token, agent_id, "R6 refinamento formato")
        _send(token, session_id, agent_id, f"análise de preço da matéria-prima {_MP}")
        follow, elapsed = _send(token, session_id, agent_id, "mostre o último resultado em tabela")
        path = _action_path(follow)
        answer = str(follow.get("answer") or follow.get("content") or "")
        _check(
            "R6 refinamento tabela",
            "/system/tables" not in path
            and (not path or "/raw-material" in path or "tabela" in answer.lower() or follow.get("toolCalls")),
            f"path={path or '(sem tool)'} elapsed={elapsed:.1f}s",
        )
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL R6 — {exc}", file=sys.stderr)
        failed += 1

    try:
        session_id = _session(token, agent_id, "MP7 MP no simulador")
        response, elapsed = _send(
            token,
            session_id,
            agent_id,
            f"Simule impacto de custo do produto {_MP}",
        )
        path = _action_path(response)
        answer = str(response.get("answer") or response.get("content") or "").lower()
        tool_meta = {}

        for call in response.get("toolCalls") or []:
            if str(call.get("name") or "") == "execute_external_action":
                tool_meta = call.get("metadata") or {}
                break

        ok = (
            not tool_meta.get("ok")
            or "/cost-impact-simulation" not in path
            or "400" in str(tool_meta.get("error") or "")
            or "pa" in answer
            or "produto acabado" in answer
            or "não" in answer
            or "nao" in answer
        )
        _check("MP7 erro MP no simulador", ok, f"path={path or '?'} elapsed={elapsed:.1f}s")
    except AssertionError:
        failed += 1
    except Exception as exc:
        print(f"FAIL MP7 — {exc}", file=sys.stderr)
        failed += 1

    if failed:
        print(f"\n{failed} cenário(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke perguntas-teste-chat-jun2026: todos os cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

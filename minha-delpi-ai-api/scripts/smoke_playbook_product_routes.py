#!/usr/bin/env python3
"""Smoke E2E — rotas de playbook otimizadas (produto + data + sessão ativa).

Valida roteamento rápido via execute_external_action (sem improvisação LLM).

Uso:
  PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway \\
    python scripts/smoke_playbook_product_routes.py
"""

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
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "90269002").strip()
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


def _assistant_pending(token: str, session_id: str) -> dict:
    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages if isinstance(messages, list) else messages.get("items", [])

    for item in reversed(items):
        if str(item.get("role") or "") != "assistant":
            continue

        meta = item.get("metadata") or {}
        pending = meta.get("activePending")

        if isinstance(pending, dict):
            return pending

    return {}


def _send(token: str, session_id: str, agent_id: str, message: str) -> tuple[dict, float]:
    started = time.monotonic()
    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "agentId": agent_id},
    )

    return response, time.monotonic() - started


def _action_path(response: dict) -> str | None:
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

    return None


def _pipeline_stages(response: dict) -> list[str]:
    admin = response.get("adminDebug") or {}
    intelligence = admin.get("intelligence") or {}
    pipeline = intelligence.get("pipeline") or {}

    return list(pipeline.get("stages") or [])


def _llm_improvised(response: dict) -> bool:
    stages = _pipeline_stages(response)
    content = str(response.get("content") or "").lower()

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
        "nao consigo consultar",
        "não consigo consultar",
    )

    return any(marker in content for marker in markers)


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK  {label}" + (f" — {detail}" if detail else ""))
        return

    print(f"FAIL {label}" + (f" — {detail}" if detail else ""), file=sys.stderr)
    raise AssertionError(label)


def main() -> int:
    failed = 0
    token = _token()
    agent_id = _agent_id(token)

    scenarios: list[tuple[str, str, str, bool]] = [
        (
            "estoque sem código pede parâmetro",
            "estoque",
            "",
            False,
        ),
        (
            "estoque com código usa /stock",
            f"estoque do produto {_PRODUCT}",
            "/stock",
            True,
        ),
        (
            "status fabril com data usa /factory-status",
            f"status fabril do produto {_PRODUCT} hoje",
            "/factory-status",
            True,
        ),
        (
            "produção com data usa /production-status",
            f"situação de produção do {_PRODUCT} hoje",
            "/production-status",
            True,
        ),
        (
            "expedição com data usa /shipping-status",
            f"inspeção final expedição produto {_PRODUCT} hoje",
            "/shipping-status",
            True,
        ),
        (
            "exclusividade MP usa /structure/exclusivity",
            f"quais matérias-primas exclusivas existem na estrutura do produto {_PRODUCT}?",
            "/structure/exclusivity",
            True,
        ),
    ]

    for title, message, expected_fragment, expect_tool in scenarios:
        try:
            session_id = _session(token, agent_id, title)
            response, elapsed = _send(token, session_id, agent_id, message)
            path = _action_path(response) or ""
            stages = _pipeline_stages(response)
            pending = _assistant_pending(token, session_id)
            answer = str(response.get("answer") or response.get("content") or "")

            if elapsed > _MAX_LATENCY_S:
                _check(title, False, f"latência {elapsed:.1f}s > {_MAX_LATENCY_S}s")
                continue

            if _llm_improvised(response):
                _check(
                    title,
                    False,
                    f"improvisação LLM stages={stages[-4:]} answer={answer[:120]!r}",
                )
                continue

            if expect_tool:
                _check(
                    title,
                    expected_fragment in path,
                    f"path={path or '?'} elapsed={elapsed:.1f}s stages={stages[-3:]}",
                )
            else:
                _check(
                    title,
                    pending.get("kind") in {"missing_product_code", "missing_date"}
                    or "código" in answer.lower()
                    or "codigo" in answer.lower()
                    or "período" in answer.lower()
                    or "periodo" in answer.lower(),
                    f"pending={pending.get('kind')} stages={stages[-3:]} elapsed={elapsed:.1f}s",
                )
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL {title} — {exc}", file=sys.stderr)
            failed += 1

    session_id = _session(token, agent_id, "continuação estoque")
    _send(token, session_id, agent_id, "estoque")
    follow, elapsed = _send(token, session_id, agent_id, _PRODUCT)
    follow_path = _action_path(follow) or ""

    try:
        _check(
            "continuação estoque após código isolado",
            "/stock" in follow_path and not _llm_improvised(follow),
            f"path={follow_path or '?'} elapsed={elapsed:.1f}s",
        )
    except AssertionError:
        failed += 1

    if failed:
        print(f"\n{failed} cenário(s) falharam", file=sys.stderr)
        return 1

    print("\nSmoke playbook rotas produto: todos os cenários passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

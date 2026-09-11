#!/usr/bin/env python3
"""Live validation — plano-02 cutovers (TU / taskPlanner / analysis dials).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_plano02_cutover_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip() or "http://localhost"
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip() or "normal"
_OUT = Path(
    os.environ.get(
        "SMOKE_EVIDENCE_PATH",
        str(
            _ROOT
            / "docs/roadmap/llm-json-decoupling/evidence/e2-plano02-cutover-live.json"
        ),
    )
)

_CASES = [
    {
        "id": "no_tool_smalltalk",
        "message": "oi, tudo bem?",
        "expect": {"min_tools": 0, "max_tools": 0},
    },
    {
        "id": "product_stock",
        "message": "qual o estoque do produto 10080001?",
        "expect": {"min_tools": 1},
    },
    {
        "id": "compound_enum",
        "message": (
            "1. estoque do produto 10080001\n"
            "2. fornecedores desse produto\n"
            "3. resume os achados"
        ),
        "expect": {"min_tools": 1, "want_task_plan": True},
    },
    {
        "id": "compare_insight",
        "message": "compara o estoque deste mês com o mês passado do produto 10080001",
        "expect": {"min_tools": 0},
    },
]


def _http(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 420,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USER,
            "password": _PASSWORD,
        }
    ).encode()
    req = urllib.request.Request(
        f"{_BASE}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"token ausente: {payload}")
    return str(token)


def _agent_id(token: str) -> str:
    explicit = os.environ.get("SMOKE_AGENT_ID", "").strip()
    if explicit:
        return explicit
    agents = _http("GET", f"{_BASE}{_CHAT}/agents?limit=20", token=token)
    items = (
        agents
        if isinstance(agents, list)
        else (agents.get("items") or agents.get("agents") or [])
    )
    if not items:
        raise RuntimeError(f"sem agents: {agents}")
    first = items[0]
    return str(first.get("id") or first.get("agentId") or "")


def _session(token: str, agent_id: str) -> str:
    created = _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "plano02-live"},
    )
    sid = created.get("id") or created.get("sessionId")
    if not sid:
        raise RuntimeError(f"session ausente: {created}")
    return str(sid)


def _send(token: str, session_id: str, message: str, agent_id: str) -> dict:
    return _http(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "agentId": agent_id,
            "responseMode": _MODE,
            "includeAdminDebug": True,
            "adminDebug": True,
        },
    )


def _assistant(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    for key in ("assistantMessage", "message"):
        node = payload.get(key)
        if isinstance(node, dict):
            return node
    return payload


def _admin(payload: dict) -> dict:
    assistant = _assistant(payload)
    for source in (assistant, payload):
        if not isinstance(source, dict):
            continue
        nested = source.get("adminDebug")
        if isinstance(nested, dict) and nested:
            return nested
        meta = source.get("metadata")
        if isinstance(meta, dict):
            nested = meta.get("adminDebug")
            if isinstance(nested, dict) and nested:
                return nested
    return {}


def _intelligence(payload: dict, admin: dict) -> dict:
    for source in (admin, _assistant(payload), payload):
        if not isinstance(source, dict):
            continue
        intel = source.get("intelligence")
        if isinstance(intel, dict):
            return intel
        meta = source.get("metadata")
        if isinstance(meta, dict) and isinstance(meta.get("intelligence"), dict):
            return meta["intelligence"]
    return {}


def _content(payload: dict) -> str:
    assistant = _assistant(payload)
    for source in (assistant, payload):
        if not isinstance(source, dict):
            continue
        for key in ("content", "answer", "text"):
            text = str(source.get(key) or "").strip()
            if text:
                return text
    return ""


def _tool_count(payload: dict, admin: dict) -> int:
    assistant = _assistant(payload)
    for source in (assistant, payload, admin):
        if not isinstance(source, dict):
            continue
        tools = source.get("toolCalls")
        if isinstance(tools, list) and tools:
            return len(tools)
        meta = source.get("metadata")
        if isinstance(meta, dict):
            tools = meta.get("toolCalls")
            if isinstance(tools, list) and tools:
                return len(tools)
        tooling = source.get("tooling")
        if isinstance(tooling, dict):
            tools = tooling.get("toolCalls")
            if isinstance(tools, list) and tools:
                return len(tools)
    return 0


def _evaluate(case: dict, payload: dict, wall_ms: float) -> dict:
    admin = _admin(payload)
    intel = _intelligence(payload, admin)
    stages = (
        admin.get("pipelineStages")
        or intel.get("pipelineStages")
        or _assistant(payload).get("pipelineStages")
        or []
    )
    shadow = (
        admin.get("authorityShadow")
        or admin.get("shadowTurnUnderstanding")
        or intel.get("authorityShadow")
        or intel.get("shadowTurnUnderstanding")
        or intel.get("turnUnderstandingShadow")
    )
    active_plan = admin.get("activeTaskPlan") or intel.get("activeTaskPlan")
    shadow_plan = admin.get("shadowTaskPlan") or intel.get("shadowTaskPlan")
    tools_n = _tool_count(payload, admin)
    content = _content(payload)
    expect = case["expect"]
    errors: list[str] = []

    if tools_n < int(expect.get("min_tools") or 0):
        errors.append(f"tools={tools_n} < min {expect.get('min_tools')}")
    if "max_tools" in expect and tools_n > int(expect["max_tools"]):
        errors.append(f"tools={tools_n} > max {expect['max_tools']}")

    if expect.get("want_task_plan"):
        stage_blob = (
            " ".join(str(s) for s in stages) if isinstance(stages, list) else str(stages)
        )
        # Compound com 2+ tools já prova decomposição operacional live;
        # plano ativo/shadow/stage reforça o dial taskPlanner.
        if tools_n < 2 and not active_plan and not shadow_plan and "task_plan" not in stage_blob:
            errors.append(
                "compound sem multi-tool nem activeTaskPlan/shadowTaskPlan/task_plan stage"
            )

    if len(content.strip()) < 2:
        errors.append("resposta vazia")

    status = "PASS" if not errors else "FAIL"
    return {
        "id": case["id"],
        "status": status,
        "wallMs": round(wall_ms, 1),
        "toolCount": tools_n,
        "hasAuthorityShadow": bool(shadow),
        "hasActiveTaskPlan": bool(active_plan),
        "hasShadowTaskPlan": bool(shadow_plan),
        "pipelineStagesSample": list(stages)[:12] if isinstance(stages, list) else stages,
        "contentChars": len(content),
        "contentPreview": content[:180],
        "adminKeys": sorted(admin.keys())[:20],
        "intelKeys": sorted(intel.keys())[:20],
        "errors": errors,
    }


def main() -> int:
    print(f"plano02 live base={_BASE} mode={_MODE}", flush=True)
    token = _token()
    print("auth ok", flush=True)
    agent_id = _agent_id(token)
    print(f"agent={agent_id}", flush=True)

    results: list[dict] = []
    for case in _CASES:
        # Renova token a cada caso (turns longos estouram expires_in).
        token = _token()
        sid = _session(token, agent_id)
        print(f"\n== {case['id']} session={sid}", flush=True)
        t0 = time.perf_counter()
        try:
            payload = _send(token, sid, case["message"], agent_id)
            wall = (time.perf_counter() - t0) * 1000
            row = _evaluate(case, payload if isinstance(payload, dict) else {}, wall)
        except Exception as exc:  # noqa: BLE001
            wall = (time.perf_counter() - t0) * 1000
            detail = str(exc)
            if isinstance(exc, urllib.error.HTTPError):
                detail = f"{exc.code}: {exc.read().decode('utf-8', errors='replace')[:300]}"
            row = {
                "id": case["id"],
                "status": "FAIL",
                "wallMs": round(wall, 1),
                "errors": [f"{type(exc).__name__}: {detail}"],
            }
        results.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)

    passed = sum(1 for r in results if r.get("status") == "PASS")
    verdict = "PASS" if passed == len(results) else "FAIL"
    evidence = {
        "schemaVersion": 1,
        "step": "E2.plano02.live",
        "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "passed": passed,
        "total": len(results),
        "cases": results,
        "notes": [
            "Valida cutovers plano-02 em HTTP live (smalltalk/stock/compound/compare).",
            "token renovado por caso; parsing alinhado a smoke_openapi_first_live.",
        ],
    }
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nVERDICT={verdict} {passed}/{len(results)} evidence={_OUT}", flush=True)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

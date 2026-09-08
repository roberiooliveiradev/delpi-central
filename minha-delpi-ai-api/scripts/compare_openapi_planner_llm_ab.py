#!/usr/bin/env python3
"""A/B — planner OpenAPI determinístico vs LLM (sempre-on no stack).

Fases:
  1) inprocess — mesma mensagem/candidatas; mede actionId, args, latência, clarify
  2) http — turno live via gateway (planner LLM sempre ligado no processo da API)

Uso:
  docker exec -e SMOKE_BASE_URL=http://delpi-gateway \\
    -w /app delpi-minha-delpi-ai-api python -u scripts/compare_openapi_planner_llm_ab.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()
_PHASE = os.environ.get("SMOKE_AB_PHASE", "all").strip().lower()
_PRODUCT = os.environ.get("SMOKE_PRODUCT_CODE", "10080022").strip()

CASES = [
    {
        "id": "stock",
        "message": f"qual o estoque do produto {_PRODUCT}?",
    },
    {
        "id": "compound-stock-price",
        "message": f"estoque e ultima compra do produto {_PRODUCT}",
    },
    {
        "id": "logistics-tracking",
        "message": "Onde esta a remessa 45871 e qual a previsao de entrega?",
        "fixture": "logistics",
    },
    {
        "id": "ambiguous-product",
        "message": f"me fala do produto {_PRODUCT}",
    },
]


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 420,
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
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    rows = agents if isinstance(agents, list) else agents.get("items") or agents.get("data") or []
    if not rows:
        raise RuntimeError("Nenhum agente disponível")
    return str(rows[0].get("id") or rows[0].get("agentId"))


def _create_session(token: str, agent_id: str, title: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": title},
    )
    session_id = payload.get("id") or payload.get("sessionId")
    if not session_id:
        raise RuntimeError(f"Sessão não criada: {payload}")
    return str(session_id)


def _send(token: str, session_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "responseMode": _RESPONSE_MODE,
            "includeAdminDebug": True,
        },
        timeout=420,
    )


def _summarize_http(response: dict) -> dict:
    assistant = response.get("assistantMessage") or response.get("message") or response
    content = str(assistant.get("content") or response.get("answer") or "")
    tool_calls = assistant.get("toolCalls") or response.get("toolCalls") or []
    actions = []
    for call in tool_calls:
        args = call.get("arguments") or {}
        meta = call.get("metadata") or {}
        actions.append(
            {
                "actionId": args.get("actionId") or meta.get("actionId"),
                "operationId": meta.get("operationId"),
                "path": meta.get("path"),
                "params": args.get("parameters") or {},
                "selectionMode": meta.get("selectionMode"),
            }
        )
    return {
        "chars": len(content),
        "preview": content[:280].replace("\n", " "),
        "tools": len(tool_calls),
        "actions": actions,
    }


def _plan_summary(plan) -> dict:
    steps = []
    for step in plan.steps or []:
        args = step.arguments or {}
        steps.append(
            {
                "actionId": step.action_id,
                "params": args.get("parameters") or {},
                "reason": (step.reason or "")[:120],
                "confidence": step.confidence,
            }
        )
    return {
        "empty": bool(plan.is_empty),
        "clarify": plan.clarify,
        "steps": steps,
        "metadata": dict(plan.metadata or {}),
    }


def phase_inprocess() -> list[dict]:
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()

    from app.application.services.openapi_llm_action_planner_service import (
        OpenApiLlmActionPlannerService,
    )
    from app.application.services.plan_external_actions_service import (
        PlanExternalActionsService,
    )
    from app.application.services.retrieve_action_candidates_service import (
        RetrieveActionCandidatesService,
    )
    from app.composition.llm_composer import make_llm_gateway
    from app.composition.root_composer import create_application
    from app.infrastructure.persistence.postgres_external_action_repository import (
        PostgresExternalActionRepository,
    )
    from tests.support.openapi_logistics_fixtures import (
        import_logistics_actions,
        logistics_allowed_action_ids,
    )

    rows: list[dict] = []
    llm = OpenApiLlmActionPlannerService(make_llm_gateway())
    repo = PostgresExternalActionRepository()

    class _LogisticsRepo:
        def __init__(self, actions: list[dict]):
            self.actions = actions

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            allowed_set = {str(item) for item in (allowed_action_ids or [])}
            return [
                action
                for action in self.actions
                if not allowed_set or str(action.get("actionId")) in allowed_set
            ][:limit]

        def list_actions(self, provider_key=None):
            return list(self.actions)

        def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
            return []

    logistics_actions = import_logistics_actions()
    logistics_allowed = logistics_allowed_action_ids(logistics_actions)
    logistics_repo = _LogisticsRepo(logistics_actions)

    app = create_application()
    with app.app_context():
        catalog = repo.list_actions()
        delpi_allowed = [
            str(item.get("actionId"))
            for item in catalog
            if str(item.get("actionId") or "").strip()
            and item.get("enabled", True) is not False
        ]
        print(f"info  catalog_actions={len(delpi_allowed)}")

        print("\n=== FASE inprocess (plan OFF vs ON) ===")
        for case in CASES:
            message = case["message"]
            use_logistics = case.get("fixture") == "logistics"
            active_repo = logistics_repo if use_logistics else repo
            allowed = logistics_allowed if use_logistics else delpi_allowed
            retriever = RetrieveActionCandidatesService(active_repo)
            candidates = retriever.retrieve(
                message,
                allowed_action_ids=allowed,
                top_k=8,
            )
            top_ids = [c.descriptor.action_id for c in candidates[:5]]

            t0 = time.time()
            plan_off = PlanExternalActionsService(llm_planner=None).plan(message, candidates)
            off_ms = int((time.time() - t0) * 1000)

            t1 = time.time()
            plan_on = PlanExternalActionsService(llm_planner=llm).plan(message, candidates)
            on_ms = int((time.time() - t1) * 1000)

            off_s = _plan_summary(plan_off)
            on_s = _plan_summary(plan_on)
            off_ids = [s["actionId"] for s in off_s["steps"]]
            on_ids = [s["actionId"] for s in on_s["steps"]]
            same = off_ids == on_ids and off_s.get("clarify") == on_s.get("clarify")

            row = {
                "caseId": case["id"],
                "message": message,
                "candidateTop": top_ids,
                "off": {**off_s, "latencyMs": off_ms},
                "on": {**on_s, "latencyMs": on_ms},
                "sameActionPlan": same,
                "deltaMs": on_ms - off_ms,
            }
            rows.append(row)
            mark = "SAME" if same else "DIFF"
            print(
                f"[{mark}] {case['id']}: off={off_ids or off_s.get('clarify')!r} "
                f"({off_ms}ms) | on={on_ids or on_s.get('clarify')!r} ({on_ms}ms) "
                f"Δ={on_ms - off_ms}ms"
            )
    return rows


def phase_http(label: str) -> list[dict]:
    print(f"\n=== FASE http ({label}) ===")
    print("info  OpenAPI planner LLM is always-on (prose/chat gateway)")

    token = _fetch_token()
    agent_id = _first_agent(token)
    rows: list[dict] = []
    for case in CASES:
        if case.get("fixture") == "logistics":
            # fixture só faz sentido inprocess; no HTTP live não há provider logistics
            continue
        session_id = _create_session(token, agent_id, f"ab-planner-{label}-{case['id']}")
        t0 = time.time()
        try:
            response = _send(token, session_id, case["message"])
            err = None
        except urllib.error.HTTPError as exc:
            response = {}
            err = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:240]}"
        except Exception as exc:
            response = {}
            err = str(exc)
        ms = int((time.time() - t0) * 1000)
        summary = _summarize_http(response) if response else {"error": err}
        summary["caseId"] = case["id"]
        summary["message"] = case["message"]
        summary["latencyMs"] = ms
        summary["label"] = label
        rows.append(summary)
        preview = summary.get("preview") or summary.get("error") or ""
        print(
            f"[{label}] {case['id']}: tools={summary.get('tools')} "
            f"chars={summary.get('chars')} ({ms}ms) | {preview[:140]}"
        )
    return rows


def main() -> int:
    report: dict = {
        "product": _PRODUCT,
        "phase": _PHASE,
        "plannerLlm": "always-on",
    }
    if _PHASE in {"all", "inprocess"}:
        report["inprocess"] = phase_inprocess()
    if _PHASE in {"all", "http"}:
        report["http"] = phase_http("live")

    out = Path(
        os.environ.get(
            "SMOKE_AB_OUT",
            f"/tmp/openapi_planner_llm_ab_{int(time.time())}.json",
        )
    )
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Smoke audit F01 / F04 / F03 — gates de domínio + HTTP self-help/SQL quando possível.

Uso (host, via gateway):
  cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python scripts/smoke_audit_familias_f01_f04_f03.py

Uso (container):
  docker exec -e SMOKE_BASE_URL=http://delpi-gateway -w /app delpi-minha-delpi-ai-api \\
    python scripts/smoke_audit_familias_f01_f04_f03.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


def _base_url() -> str:
    explicit = os.environ.get("SMOKE_BASE_URL", "").strip()
    if explicit:
        return explicit
    if os.path.isdir("/app"):
        return "http://delpi-gateway"
    return "http://localhost"


_BASE = _base_url()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USER = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_SKIP_HTTP = os.environ.get("SMOKE_SKIP_HTTP", "").strip() in {"1", "true", "yes"}


@dataclass
class CaseResult:
    case_id: str
    family: str
    ok: bool
    detail: str


def _ok(case_id: str, family: str, ok: bool, detail: str = "") -> CaseResult:
    status = "PASS" if ok else "FAIL"
    print(f"{status} {case_id} [{family}] {detail}".rstrip())
    return CaseResult(case_id, family, ok, detail)


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 180,
) -> dict:
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
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{_BASE}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Token ausente: {payload}")
    return str(token)


def _first_agent(token: str) -> str:
    agents = _request("GET", f"{_BASE}{_CHAT}/agents?limit=30", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])
    for agent in items:
        if agent.get("enabled") and "delpi" in str(agent.get("name") or "").lower():
            return str(agent["id"])
    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])
    if items:
        return str(items[0]["id"])
    raise RuntimeError("Nenhum agente disponível")


def _send(token: str, message: str, *, agent_id: str | None) -> dict:
    session_body: dict[str, Any] = {
        "title": f"Audit smoke: {message[:48]}",
    }
    if agent_id:
        session_body["agentId"] = agent_id
    session = _request("POST", f"{_BASE}{_CHAT}/sessions", token=token, body=session_body)
    session_id = str(session.get("id") or "").strip()
    if not session_id:
        raise RuntimeError(f"Sessão sem id: {session}")

    body: dict[str, Any] = {
        "message": message,
        "responseMode": "normal",
        "includeAdminDebug": True,
    }
    if agent_id:
        body["agentId"] = agent_id
    return _request(
        "POST",
        f"{_BASE}{_CHAT}/sessions/{session_id}/messages",
        token=token,
        body=body,
    )


def _answer_text(payload: dict) -> str:
    direct = str(payload.get("content") or payload.get("answer") or "").strip()
    if direct:
        return direct
    assistant = payload.get("assistantMessage") or payload.get("assistant") or {}
    if isinstance(assistant, dict):
        return str(
            assistant.get("content")
            or assistant.get("text")
            or assistant.get("answer")
            or ""
        ).strip()
    return str(assistant or "").strip()


def _admin(payload: dict) -> dict:
    debug = payload.get("adminDebug")
    if isinstance(debug, dict):
        return debug
    meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    nested = meta.get("adminDebug") if isinstance(meta.get("adminDebug"), dict) else {}
    return nested if isinstance(nested, dict) else {}


def run_domain_gates() -> list[CaseResult]:
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()

    from app.application.services.chat_capabilities_service import ChatCapabilitiesService
    from app.application.services.chat_guided_flow_service import ChatGuidedFlowService
    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )
    from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prose_formatting_service import (
        ChatAdvancedSqlSpecialistProseFormattingService as Fmt,
    )
    from app.domain.services.chat_advanced_sql_specialist_service import (
        ChatAdvancedSqlSpecialistService,
    )
    from app.domain.services.chat_intent_router_service import ChatIntentRouterService
    from app.domain.services.chat_sql_authoring_guidance_service import (
        ChatSqlAuthoringGuidanceService,
    )
    from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
    from app.application.services.chat_common_chat_operational_guidance_service import (
        ChatCommonChatOperationalGuidanceService,
    )
    from app.application.services.chat_workspace_agent_activation_service import (
        ChatWorkspaceAgentActivationService,
    )

    class FakeRepo:
        def __init__(self, actions: list[dict]) -> None:
            self.actions = actions

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            return self.actions

        def list_actions(self, provider_key=None):
            return self.actions

    results: list[CaseResult] = []

    # --- F01 ---
    flow = ChatGuidedFlowService.build_for_message("como ativo o agente?")
    results.append(
        _ok(
            "F01.1",
            "agent",
            bool(flow and flow.get("id") == "agent"),
            f"flowId={flow.get('id') if flow else None}",
        )
    )
    help_txt = ChatCapabilitiesService._answer_topic_help("agentHelp") or ""
    results.append(
        _ok(
            "F01.1b",
            "agent",
            "Como usar" in help_txt or "composer" in help_txt.lower(),
            "agentHelp instrui ativação",
        )
    )
    msg = "qual agente consulta produto?"
    results.append(
        _ok(
            "F01.2a",
            "agent",
            not ChatSqlSafetyService.looks_like_sql_payload(msg),
            "não SQL payload",
        )
    )
    results.append(
        _ok(
            "F01.2b",
            "agent",
            not ChatAdvancedSqlSpecialistService.should_activate(msg),
            "não ativa SQL specialist",
        )
    )
    results.append(
        _ok(
            "F01.2c",
            "agent",
            ChatCapabilitiesService.classify_help_topic(msg) == "agent",
            f"topic={ChatCapabilitiesService.classify_help_topic(msg)}",
        )
    )
    flow2 = ChatGuidedFlowService.build_for_message(msg)
    results.append(
        _ok(
            "F01.2d",
            "agent",
            bool(flow2 and flow2.get("id") == "agent"),
            f"flowId={flow2.get('id') if flow2 else None}",
        )
    )
    stock_msg = "qual o estoque do produto 10080001?"
    common_ws = {"userActivatedAgent": False, "actionsEnabled": False}
    needs_agent = ChatCommonChatOperationalGuidanceService.requires_agent(
        stock_msg,
        workspace_context=common_ws,
    )
    guidance = ChatCommonChatOperationalGuidanceService.resolve_direct_answer(
        stock_msg,
        workspace_context=common_ws,
    )
    tools_off = not ChatWorkspaceAgentActivationService.operational_tools_enabled(
        common_ws
    )
    results.append(
        _ok(
            "F01.3",
            "agent",
            tools_off and needs_agent and bool(guidance),
            f"tools_off={tools_off} needs_agent={needs_agent} has_guidance={bool(guidance)}",
        )
    )

    # --- F04 ---
    sql_msg = "crie um sql que liste os 10 primeiros produtos do grupo 1008"
    results.append(
        _ok(
            "F04.1a",
            "sql_authoring",
            ChatSqlAuthoringGuidanceService.is_custom_sql_authoring(sql_msg),
            "custom authoring",
        )
    )
    route = ChatIntentRouterService.classify(sql_msg)
    results.append(
        _ok(
            "F04.1b",
            "sql_authoring",
            route.sub_intent == "sql_generate" or route.decision == "sql_route",
            f"intent={route.intent} sub={route.sub_intent} decision={route.decision}",
        )
    )
    actions = [
        {
            "actionId": "api_delpi.produ_o_operacional.get_production_schedule_today",
            "method": "GET",
            "path": "/production/schedule/today",
            "operationId": "get_production_schedule_today",
            "summary": "Produtos programados para produzir na data",
            "selectionScore": 0.99,
            "parametersSchema": [{"name": "reference_date"}, {"name": "branch"}],
        },
        {
            "actionId": "search-products",
            "method": "GET",
            "path": "/products/search",
            "operationId": "search_products",
            "summary": "Busca produtos por grupo",
            "selectionScore": 0.85,
            "parametersSchema": [{"name": "group_code"}],
        },
    ]
    selected = ExternalActionSelectionService(FakeRepo(actions)).select_action(
        sql_msg,
        allowed_action_ids=[a["actionId"] for a in actions],
    )
    results.append(
        _ok(
            "F04.1c",
            "sql_authoring",
            selected is None,
            f"selected={selected}",
        )
    )
    fixed = Fmt.normalize_protheus_sql_answer(
        "```sql\nSELECT B1_COD, B1_DESC FROM SB1010 WHERE D_E_L_E_T_ = ''\n```",
        message="ajuste o sql para trazer os top 10",
    )
    results.append(
        _ok(
            "F04.4",
            "sql_authoring",
            "SB1010" in fixed
            and "TOP 10" in fixed.upper()
            and "A1_COD" not in fixed,
            "preserva SB1 + TOP 10",
        )
    )
    leaked = (
        "ENTREGA OBRIGATÓRIA: responda com bloco\n\n"
        "```sql\nSELECT TOP 10 B1_COD FROM SB1010 WHERE B1_GRUPO='1008'\n```\n\n"
        "antes de qualquer outro conteúdo."
    )
    clean = Fmt.format_sql_authoring_answer(leaked)
    results.append(
        _ok(
            "F04.leak",
            "sql_authoring",
            "ENTREGA" not in clean.upper() and "SB1010" in clean,
            "strip leak",
        )
    )

    # --- F03 sample (selection should pick stock when asked stock) ---
    stock_actions = [
        {
            "actionId": "stock-action",
            "method": "GET",
            "path": "/products/{code}/stock",
            "operationId": "get_product_stock",
            "summary": "Estoque do produto",
            "selectionScore": 0.4,
            "parametersSchema": [{"name": "code"}],
        },
        {
            "actionId": "api_delpi.produ_o_operacional.get_production_schedule_today",
            "method": "GET",
            "path": "/production/schedule/today",
            "operationId": "get_production_schedule_today",
            "summary": "Produtos programados para produzir na data",
            "selectionScore": 0.95,
            "parametersSchema": [{"name": "reference_date"}],
        },
    ]
    stock_sel = ExternalActionSelectionService(FakeRepo(stock_actions)).select_action(
        "qual o estoque do produto 10080001?",
        allowed_action_ids=[a["actionId"] for a in stock_actions],
    )
    stock_id = (
        ((stock_sel or {}).get("arguments") or {}).get("actionId")
        if isinstance(stock_sel, dict)
        else None
    )
    results.append(
        _ok(
            "F03.1",
            "operational_rest",
            stock_id == "stock-action",
            f"actionId={stock_id}",
        )
    )
    sched_sel = ExternalActionSelectionService(FakeRepo(stock_actions)).select_action(
        "quais produtos programados para produzir hoje?",
        allowed_action_ids=[a["actionId"] for a in stock_actions],
    )
    sched_id = (
        ((sched_sel or {}).get("arguments") or {}).get("actionId")
        if isinstance(sched_sel, dict)
        else None
    )
    results.append(
        _ok(
            "F03.6",
            "operational_rest",
            sched_id == "api_delpi.produ_o_operacional.get_production_schedule_today"
            or (sched_id and "schedule" in str(sched_id).lower()),
            f"actionId={sched_id}",
        )
    )

    return results


def run_http(results: list[CaseResult]) -> list[CaseResult]:
    if _SKIP_HTTP:
        print("SKIP HTTP (SMOKE_SKIP_HTTP=1)")
        return results

    print(f"\n--- HTTP via {_BASE} ---")
    try:
        token = _token()
        agent_id = _first_agent(token)
        print(f"agentId={agent_id}")
    except Exception as exc:  # noqa: BLE001
        results.append(_ok("HTTP.auth", "infra", False, str(exc)))
        return results

    # F01.1 live help
    try:
        payload = _send(token, "como ativo o agente?", agent_id=None)
        answer = _answer_text(payload)
        debug = _admin(payload)
        intent = (debug.get("intentRoute") or {}) if isinstance(debug, dict) else {}
        tools = debug.get("tooling") if isinstance(debug.get("tooling"), dict) else {}
        tool_calls = tools.get("toolCalls") if isinstance(tools, dict) else None
        if not isinstance(tool_calls, list):
            tool_calls = payload.get("toolCalls") if isinstance(payload.get("toolCalls"), list) else []
        n_tools = len(tool_calls)
        low = answer.lower()
        ok = (
            ("+" in answer or "composer" in low or "agente" in low)
            and "sb1010" not in low
            and n_tools == 0
        )
        results.append(
            _ok(
                "F01.1-live",
                "agent",
                ok,
                f"tools={n_tools} intent={intent.get('subIntent') or intent.get('intent')} "
                f"ans={answer[:80]!r}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(_ok("F01.1-live", "agent", False, str(exc)))

    # F01.2 live
    try:
        payload = _send(token, "qual agente consulta produto?", agent_id=None)
        answer = _answer_text(payload)
        debug = _admin(payload)
        tools = debug.get("tooling") if isinstance(debug.get("tooling"), dict) else {}
        selected = tools.get("selectedExternalAction") if isinstance(tools, dict) else None
        low = answer.lower()
        ok = (
            "select " not in low
            and "sb1010" not in low
            and selected is None
            and ("agente" in low or "+" in answer or "composer" in low)
        )
        results.append(
            _ok(
                "F01.2-live",
                "agent",
                ok,
                f"selected={selected} ans={answer[:90]!r}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(_ok("F01.2-live", "agent", False, str(exc)))

    # F04.1 live with agent — must not call production schedule
    try:
        payload = _send(
            token,
            "crie um sql que liste os 10 primeiros produtos do grupo 1008",
            agent_id=agent_id,
        )
        answer = _answer_text(payload)
        debug = _admin(payload)
        intent = debug.get("intentRoute") if isinstance(debug.get("intentRoute"), dict) else {}
        tools = debug.get("tooling") if isinstance(debug.get("tooling"), dict) else {}
        evidence = (
            (debug.get("intelligence") or {}).get("evidenceRefs")
            if isinstance(debug.get("intelligence"), dict)
            else None
        )
        selected = tools.get("selectedExternalAction") if isinstance(tools, dict) else None
        path = ""
        op = ""
        if isinstance(selected, dict):
            path = str(selected.get("path") or "")
            op = str(selected.get("operationId") or "")
        if isinstance(evidence, list) and evidence:
            first = evidence[0] if isinstance(evidence[0], dict) else {}
            path = path or str(first.get("path") or "")
            op = op or str(first.get("operationId") or "")
        for call in payload.get("toolCalls") or []:
            if not isinstance(call, dict):
                continue
            meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
            path = path or str(meta.get("path") or "")
            op = op or str(meta.get("operationId") or "")
        low = answer.lower()
        has_sql = "```sql" in low or "select " in low
        bad_schedule = "schedule" in path.lower() or "production_schedule" in op.lower()
        leak = "entrega obrigatória" in low or "modo: create" in low
        ok = has_sql and not bad_schedule and not leak
        results.append(
            _ok(
                "F04.1-live",
                "sql_authoring",
                ok,
                f"sub={intent.get('subIntent')} path={path or '-'} op={op or '-'} "
                f"sql={has_sql} leak={leak} ans={answer[:70]!r}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(_ok("F04.1-live", "sql_authoring", False, str(exc)))

    # F03.1 live stock with agent
    try:
        payload = _send(
            token,
            "qual o estoque do produto 10080001?",
            agent_id=agent_id,
        )
        debug = _admin(payload)
        tools = debug.get("tooling") if isinstance(debug.get("tooling"), dict) else {}
        selected = tools.get("selectedExternalAction") if isinstance(tools, dict) else None
        path = str((selected or {}).get("path") or "") if isinstance(selected, dict) else ""
        op = str((selected or {}).get("operationId") or "") if isinstance(selected, dict) else ""
        if not path:
            for call in payload.get("toolCalls") or []:
                if not isinstance(call, dict):
                    continue
                meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
                cand = str(meta.get("path") or "")
                if cand:
                    path = cand
                    op = str(meta.get("operationId") or op)
                    break
        ok = "/stock" in path.lower() or "stock" in op.lower()
        results.append(
            _ok(
                "F03.1-live",
                "operational_rest",
                ok,
                f"path={path or selected or '-'} op={op or '-'}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(_ok("F03.1-live", "operational_rest", False, str(exc)))

    return results


def main() -> int:
    print("=== Audit smoke F01 / F04 / F03 ===\n--- Domain gates ---")
    results = run_domain_gates()
    results = run_http(results)

    failed = [r for r in results if not r.ok]
    print(
        f"\n=== RESUMO === {len(results) - len(failed)}/{len(results)} PASS "
        f"({len(failed)} FAIL)"
    )
    for item in failed:
        print(f"  FAIL {item.case_id}: {item.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

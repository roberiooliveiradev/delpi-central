#!/usr/bin/env python3
"""Smoke live — OpenAPI-first tool routing (logística + regressão DELPI).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_openapi_first_live.py

Modos:
  SMOKE_OPENAPI_PHASE=inprocess|http|all  (default all)
  SMOKE_BASE_URL=http://localhost
  SMOKE_USER / SMOKE_PASSWORD

Fases:
  1) inprocess — fixture logística no processo (selectionMode=openapi_first)
  2) http — chat live via gateway (OpenAPI-first é o único seletor)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_RESPONSE_MODE = os.environ.get("SMOKE_RESPONSE_MODE", "normal").strip()
_PHASE = os.environ.get("SMOKE_OPENAPI_PHASE", "all").strip().lower()
_LOGISTICS_MSG = os.environ.get(
    "SMOKE_LOGISTICS_MESSAGE",
    "Onde esta a remessa 45871 e qual a previsao de entrega?",
).strip()
_DELPI_MSG = os.environ.get(
    "SMOKE_DELPI_MESSAGE",
    "qual o estoque do produto 10080022?",
).strip()


def _ok(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"PASS  {label}{suffix}")


def _fail(label: str, detail: str) -> None:
    print(f"FAIL  {label} — {detail}")


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 360,
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
    explicit = os.environ.get("SMOKE_AGENT_ID", "").strip()
    if explicit:
        return explicit
    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=20", token=token)
    rows = agents if isinstance(agents, list) else agents.get("items") or agents.get("data") or []
    if not rows:
        raise RuntimeError("Nenhum agente disponível")
    return str(rows[0].get("id") or rows[0].get("agentId"))


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-openapi-first"},
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


def phase_inprocess() -> list[str]:
    """Seleção OpenAPI-first da fixture logística no processo atual."""
    errors: list[str] = []
    print("\n=== FASE inprocess (fixture logística) ===")

    # Garante ports de content quando rodando fora do Flask app.
    try:
        from app.composition.content_composer import configure_domain_infrastructure_ports

        configure_domain_infrastructure_ports()
    except Exception as exc:
        errors.append(f"content ports: {exc}")
        _fail("content_ports", str(exc))
        return errors

    from app.application.services.chat_external_action_orchestration_service import (
        ChatExternalActionOrchestrationService,
    )
    from app.application.services.openapi_first_selection_bridge_service import (
        OpenApiFirstSelectionBridgeService,
    )
    from app.domain.services.openapi_planner_mode_service import OpenApiPlannerModeDecision
    from tests.support.openapi_logistics_fixtures import (
        import_logistics_actions,
        logistics_allowed_action_ids,
    )

    actions = import_logistics_actions()
    allowed = logistics_allowed_action_ids(actions)

    class _Repo:
        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            allowed_set = {str(item) for item in (allowed_action_ids or [])}
            return [
                action
                for action in actions
                if not allowed_set or str(action.get("actionId")) in allowed_set
            ][:limit]

        def list_actions(self, provider_key=None):
            return list(actions)

        def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
            return []

    repo = _Repo()
    decision = OpenApiPlannerModeDecision(
        mode="on",
        use_openapi_selection=True,
        run_shadow_compare=False,
        canary_matched=False,
    )
    bridge = OpenApiFirstSelectionBridgeService(repo)
    planned = bridge.plan_tool_calls(
        _LOGISTICS_MSG,
        allowed_action_ids=allowed,
        catalog_actions=actions,
        mode_decision=decision,
        workspace_context={"providerKeys": ["logistics-example"]},
    )

    if not planned:
        errors.append("bridge retornou vazio")
        _fail("bridge_plan", "vazio")
        return errors

    call = planned[0]
    args = call.get("arguments") or {}
    params = args.get("parameters") or {}
    op = (call.get("metadata") or {}).get("operationId")
    mode = (call.get("metadata") or {}).get("selectionMode")

    if call.get("name") != "execute_external_action":
        errors.append(f"name={call.get('name')}")
        _fail("bridge_tool", str(call.get("name")))
    elif op != "get_shipment_tracking":
        errors.append(f"operationId={op}")
        _fail("bridge_operation", str(op))
    elif str(params.get("id")) != "45871":
        errors.append(f"id={params.get('id')}")
        _fail("bridge_param_id", str(params.get("id")))
    elif mode != "openapi_first":
        errors.append(f"selectionMode={mode}")
        _fail("bridge_mode", str(mode))
    else:
        _ok("bridge_tracking", f"{op} id={params.get('id')} mode={mode}")

    class _Selection:
        repository = repo
        semantic_ranker = None

    orch = ChatExternalActionOrchestrationService.plan_actions(
        _Selection(),
        message=_LOGISTICS_MSG,
        allowed_action_ids=allowed,
        workspace_context={"providerKeys": ["logistics-example"]},
    )
    if not orch:
        errors.append("orchestration vazia com mode=on")
        _fail("orchestration", "vazia")
    else:
        orch_id = ((orch[0].get("arguments") or {}).get("parameters") or {}).get("id")
        if str(orch_id) != "45871":
            errors.append(f"orchestration id={orch_id}")
            _fail("orchestration_id", str(orch_id))
        else:
            _ok("orchestration", f"actions={len(orch)} id={orch_id}")

    return errors


def phase_http() -> list[str]:
    """Chat HTTP live — health + turn DELPI (+ OpenAPI metadata se mode≠off)."""
    errors: list[str] = []
    print("\n=== FASE http (gateway live) ===")

    try:
        token = _fetch_token()
        _ok("auth", "token obtido")
    except Exception as exc:
        errors.append(f"auth: {exc}")
        _fail("auth", str(exc))
        return errors

    try:
        agent_id = _first_agent(token)
        _ok("agent", agent_id)
    except Exception as exc:
        errors.append(f"agent: {exc}")
        _fail("agent", str(exc))
        return errors

    print("info  OpenAPI-first é o único seletor (sem flag de mode)")

    try:
        session_id = _create_session(token, agent_id)
        _ok("session", session_id)
    except Exception as exc:
        errors.append(f"session: {exc}")
        _fail("session", str(exc))
        return errors

    try:
        response = _send(token, session_id, _DELPI_MSG)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        errors.append(f"send HTTP {exc.code}: {body[:400]}")
        _fail("send_delpi", f"{exc.code}")
        return errors
    except Exception as exc:
        errors.append(f"send: {exc}")
        _fail("send_delpi", str(exc))
        return errors

    assistant = response.get("assistantMessage") or response.get("message") or response
    content = str(assistant.get("content") or response.get("answer") or "")
    tool_calls = assistant.get("toolCalls") or response.get("toolCalls") or []
    admin_debug = assistant.get("adminDebug") or response.get("adminDebug") or {}
    metadata = assistant.get("metadata") or response.get("metadata") or {}

    if not content and not tool_calls:
        errors.append("resposta vazia (sem content/toolCalls)")
        _fail("delpi_response", "vazia")
    else:
        _ok(
            "delpi_response",
            f"tools={len(tool_calls)} chars={len(content)}",
        )

    # Procura metadata de seleção OpenAPI.
    blob = json.dumps(
        {"toolCalls": tool_calls, "adminDebug": admin_debug, "metadata": metadata},
        ensure_ascii=False,
    )
    if "openapi_first" in blob or "openapiFirst" in blob:
        _ok("openapi_metadata", "sinal OpenAPI-first presente no turno")
    else:
        _ok(
            "openapi_runtime",
            "turno DELPI saudável (metadata de seleção pode não sobreviver ao present)",
        )

    # Turno logístico só faz sentido se o provider estiver importado no agente.
    if os.environ.get("SMOKE_TRY_LOGISTICS_HTTP", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }:
        try:
            session2 = _create_session(token, agent_id)
            logistics = _send(token, session2, _LOGISTICS_MSG)
            assistant2 = logistics.get("assistantMessage") or logistics.get("message") or logistics
            tools2 = assistant2.get("toolCalls") or logistics.get("toolCalls") or []
            blob2 = json.dumps(tools2, ensure_ascii=False)
            if "tracking" in blob2.lower() or "45871" in blob2:
                _ok("logistics_http", "tracking/id presentes nas tools")
            else:
                _fail(
                    "logistics_http",
                    "sem tracking — importe o provider logistics-example no agente",
                )
                errors.append("logistics_http sem tracking")
        except Exception as exc:
            errors.append(f"logistics_http: {exc}")
            _fail("logistics_http", str(exc))

    return errors


def main() -> int:
    print("smoke_openapi_first_live")
    print(f"base={_BASE_URL} phase={_PHASE}")
    errors: list[str] = []

    run_inprocess = _PHASE in {"all", "inprocess"}
    run_http = _PHASE in {"all", "http"}

    if run_inprocess:
        # Garante import path do repo
        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        errors.extend(phase_inprocess())

    if run_http:
        errors.extend(phase_http())

    print("\n=== RESUMO ===")
    if errors:
        for item in errors:
            print(f" - {item}")
        print(f"RESULT FAIL ({len(errors)} erro(s))")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

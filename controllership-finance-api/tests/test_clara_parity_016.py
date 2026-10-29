"""CLARA — paridade funcional Portal × CLARA (execução 016, não-PG).

Cobre:
- tools READ novas delegando na função de rota canônica (_call_route):
  envelope ok/error preservado, HTTPException → erro tipado MCP.
- contrato de cada capability do catálogo governado (gate, params,
  resource_type, key, execute/verify/postcondition).
- gates efetivos: manage/dre fail-closed na identidade injetada,
  provider ausente ⇒ GateUnavailable.
- flag `destructive` nas operações classe D.
- presenters: toda capability com displayable=True e chaves mínimas.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException

from controllership_finance_app.application.clara import (
    governed_writes as gw,
)
from controllership_finance_app.application.clara import (
    operation_presentation as opres,
)
from controllership_finance_app.interface.mcp import tool_bridge
from controllership_finance_app.interface.mcp.constants import (
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)


# ------------------------------------------------------------------
# _call_route — envelope tipado idêntico ao Portal
# ------------------------------------------------------------------


def _json_response(payload: dict, status: int = 200):
    import json as _json

    from fastapi.responses import JSONResponse

    return JSONResponse(payload, status_code=status)


def test_call_route_passthrough_dict():
    route = lambda _request, **_kw: {  # noqa: E731
        "period": "2026-09",
        "rows": [],
    }
    res = tool_bridge._call_route(route, None, period="2026-09")
    assert res.is_error is False
    assert res.structured_content["data"]["period"] == "2026-09"


def test_call_route_envelope_ok():
    route = lambda _request: _json_response(  # noqa: E731
        {"success": True, "data": {"x": 1}, "message": "ok"}
    )
    res = tool_bridge._call_route(route, None)
    assert res.is_error is False
    assert res.structured_content["data"]["x"] == 1


def test_call_route_envelope_error():
    route = lambda _request: _json_response(  # noqa: E731
        {
            "success": False,
            "message": "escopo indisponível",
            "data": {"error": {"code": "scope_unavailable"}},
        },
        status=403,
    )
    res = tool_bridge._call_route(route, None)
    assert res.is_error is True
    data = res.structured_content["data"]
    assert data["error"]["code"] == "scope_unavailable"
    assert res.structured_content["status_code"] == 403


def test_call_route_http_exception_propagates_to_guard():
    def route(_request):
        raise HTTPException(status_code=403, detail="Forbidden")

    with pytest.raises(HTTPException):
        tool_bridge._call_route(route, None)


def test_authz_literal_maps_to_permission_error():
    def route(_request):
        raise RuntimeError("Unauthorized")

    with pytest.raises(PermissionError):
        tool_bridge._call_route(route, None)


def test_handle_tool_error_unauthorized_401():
    res = tool_bridge.handle_tool_error(PermissionError("Unauthorized"))
    assert res.is_error is True
    assert res.structured_content["status_code"] == 401


# ------------------------------------------------------------------
# Superfície: cada tool READ nova existe no bridge e no registry
# ------------------------------------------------------------------

READ_PARITY_TOOLS = (
    "list_competences",
    "get_competence",
    "get_checklist_item",
    "get_closing_cockpit",
    "list_my_tasks",
    "get_pendency",
    "list_p3_events",
    "get_package",
    "get_document",
    "get_item_validation",
    "lookup_participants",
    "get_financial_settlements",
    "get_financial_settlements_summary",
    "get_stock_inventory",
    "get_stock_movements",
    "get_work_in_process",
    "get_stock_reconciliation",
    "get_report_matrix",
    "list_closing_catalogs",
    "list_catalog_entries",
    "list_checklist_templates",
    "get_checklist_template_version",
    "list_received_deliveries",
    "get_received_delivery",
    "get_received_document",
)


@pytest.mark.parametrize("name", READ_PARITY_TOOLS)
def test_read_tool_registered_and_callable(name):
    assert name in MCP_TOOL_NAMES
    assert TOOL_CLASS[name] == "READ"
    assert callable(getattr(tool_bridge, f"tool_{name}"))


def test_read_tool_delegates_to_canonical_route(monkeypatch):
    """get_competence deve chamar a rota canônica da competência."""
    from controllership_finance_app.interface.http.routes import (
        competences_routes,
    )

    seen = {}

    def fake(request, period):
        seen["period"] = period
        return {"period": period}

    monkeypatch.setattr(
        tool_bridge,
        "_user_and_access",
        lambda: (object(), MagicMock()),
    )
    monkeypatch.setattr(
        competences_routes, "get_closing_competence", fake
    )
    res = tool_bridge.tool_get_competence("2026-09")
    assert res.is_error is False
    assert seen["period"] == "2026-09"


# ------------------------------------------------------------------
# Catálogo governado — contrato completo por capability
# ------------------------------------------------------------------

NEW_CAPS = [
    "competence.open",
    "pendency.create",
    "pendency.reassign",
    "pendency.transition",
    "p3.confirm_cutoff",
    "p3.upsert_reconciliation",
    "p3.revalidate",
    "package.finalize",
    "package.reopen",
    "package.complement",
    "package.submit_review",
    "package.start_review",
    "package.confirm_terminal_rejection",
    "package.revert_terminal_rejection",
    "item.reverse_decision",
    "item.mark_not_applicable",
    "item.revert_not_applicable",
    "item.cancel",
    "item.create_exceptional",
    "item.request_correction",
    "item.review_correction",
    "document.post_message",
    "document.cancel",
    "document.answer_adjustment",
    "received.post_message",
    "received.create_adjustment",
    "received.confirm_adjustment",
    "catalog.entry_create",
    "catalog.entry_update",
    "catalog.entry_deactivate",
    "catalog.entry_reactivate",
    "checklist.draft_create",
    "checklist.draft_update",
    "checklist.version_submit",
    "checklist.version_return",
    "checklist.version_discard",
    "checklist.version_publish",
    "checklist.version_inactivate",
    "checklist.doc_requirement",
]

DESTRUCTIVE_CAPS = {
    "package.confirm_terminal_rejection",
    "item.cancel",
    "document.cancel",
    "catalog.entry_deactivate",
    "checklist.version_discard",
    "checklist.version_inactivate",
}


def _writers() -> gw.ClaraGovernedWrites:
    return gw.ClaraGovernedWrites(identity_provider=lambda: {
        "subject": "00000000-0000-0000-0000-000000000001",
        "name": "Op",
        "is_manage": True,
        "is_dre": False,
    })


def test_catalog_covers_new_portal_operations():
    caps = {c["capability"] for c in _writers().capabilities()}
    for c in NEW_CAPS:
        assert c in caps, c


@pytest.mark.parametrize("cap", NEW_CAPS)
def test_capability_contract_complete(cap):
    spec = _writers()._capability_table()[cap]
    assert spec["required_params"]
    assert spec["gate"] in {"access", "manage", "dre"}
    assert spec["resource_type"]
    for key in ("describe", "execute", "verify",
                "postcondition", "resource_key"):
        assert callable(spec[key]), f"{cap}.{key}"


@pytest.mark.parametrize("cap", NEW_CAPS)
def test_capability_presenter_displayable(cap):
    spec = _writers()._capability_table()[cap]
    params = {k: "x" for k in spec["required_params"]}
    p = opres.present_operation(cap, params)
    assert p["displayable"] is True, cap
    for key in ("action", "target", "summary"):
        assert p.get(key), f"{cap}.{key}"


def test_destructive_flags_on_class_d():
    table = _writers()._capability_table()
    for cap in DESTRUCTIVE_CAPS:
        assert table[cap].get("destructive") is True, cap
    flagged = {n for n, s in table.items() if s.get("destructive")}
    assert flagged == DESTRUCTIVE_CAPS


# ------------------------------------------------------------------
# Gates efetivos — identidade real injetada, fail-closed
# ------------------------------------------------------------------


def _writers_with(**identity):
    ident = {
        "subject": "00000000-0000-0000-0000-000000000001",
        "name": "Op",
        "is_manage": False,
        "is_dre": False,
    }
    ident.update(identity)
    return gw.ClaraGovernedWrites(identity_provider=lambda: ident)


# Mapa Portal→CLARA: rotas com `authorized_admin`/`_require_manage`.
MANAGE_CAPS = (
    "catalog.entry_create",
    "catalog.entry_update",
    "catalog.entry_deactivate",
    "catalog.entry_reactivate",
    "checklist.draft_create",
    "checklist.draft_update",
    "checklist.version_submit",
    "checklist.version_return",
    "checklist.version_discard",
    "checklist.version_publish",
    "checklist.version_inactivate",
    "checklist.doc_requirement",
    "clarification.resolve",
    "evidence.decide_item_set",
    "evidence.decide_version",
    "item.reverse_decision",
    "item.review_correction",
    "p3.confirm_cutoff",
    "p3.revalidate",
    "p3.upsert_reconciliation",
    "package.assignment_create",
    "package.assignment_deactivate",
    "package.complement",
    "package.finalize",
    "package.reopen",
    "package.submit_review",
    "pendency.confirm_classification",
    "pendency.reassign",
)

# Rotas `authorized_user` — acesso regular (regras de negócio
# adicionais ficam no repositório, como no Portal).
ACCESS_CAPS = (
    "clarification.open",
    "competence.open",
    "document.answer_adjustment",
    "document.cancel",
    "document.post_message",
    "item.cancel",
    "item.create_exceptional",
    "item.mark_not_applicable",
    "item.request_correction",
    "item.revert_not_applicable",
    "package.confirm_terminal_rejection",
    "package.revert_terminal_rejection",
    "package.start_review",
    "pendency.claim",
    "pendency.create",
    "pendency.transition",
    "review.record_decision",
)


def test_gate_map_matches_portal_routes():
    table = _writers()._capability_table()
    for cap in MANAGE_CAPS:
        assert table[cap]["gate"] == "manage", cap
    for cap in ACCESS_CAPS:
        assert table[cap]["gate"] == "access", cap
    for cap in ("received.post_message", "received.create_adjustment",
                "received.confirm_adjustment"):
        assert table[cap]["gate"] == "dre", cap


def test_manage_gate_denies_plain_access_user():
    w = _writers_with()
    for cap in MANAGE_CAPS:
        with pytest.raises(gw.OperationForbidden):
            w._check_gate(cap)


def test_manage_gate_allows_manager():
    w = _writers_with(is_manage=True)
    for cap in MANAGE_CAPS:
        w._check_gate(cap)  # não levanta


def test_dre_gate_allows_dre_and_denies_plain_access():
    w_dre = _writers_with(is_dre=True)
    for cap in ("received.post_message", "received.create_adjustment",
                "received.confirm_adjustment"):
        w_dre._check_gate(cap)
    w_plain = _writers_with()
    for cap in ("received.post_message", "received.create_adjustment",
                "received.confirm_adjustment"):
        with pytest.raises(gw.OperationForbidden):
            w_plain._check_gate(cap)


def test_access_gate_never_consumes_dre_or_manage():
    """`access` é garantido no entry MCP — não vira implícito."""
    w = _writers_with()
    assert w._check_gate("pendency.claim") == {}


def test_gate_fails_closed_without_identity_provider():
    w = gw.ClaraGovernedWrites()
    with pytest.raises(gw.GateUnavailable):
        w._check_gate("catalog.entry_create")


# ------------------------------------------------------------------
# Batch — falha de pós-condição produz UNKNOWN honesto
# ------------------------------------------------------------------


def test_batch_unverified_maps_to_unknown():
    """O ramo outcome_verification_failed existe e classifica UNKNOWN."""
    from controllership_finance_app.application.clara import (
        batch_orchestrator as bo,
    )
    import inspect

    src = inspect.getsource(bo.ClaraBatchOrchestrator._execute_operation)
    assert "outcome_verification_failed" in src
    assert '"UNKNOWN"' in src
    assert '"unverified"' in src

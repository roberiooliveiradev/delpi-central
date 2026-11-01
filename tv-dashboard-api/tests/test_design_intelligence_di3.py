"""DI-3 — assisted composition via the canonical suggest_change path.

Scenarios A–E (non-technical business requests) reach
PresentationCommandPlannerService.plan → typed ops payload +
designMethodology advisory — through analyze.intent_materialization.
No mutations, no external channel.
"""
from __future__ import annotations

from unittest.mock import patch

from test_vista_mcp_write_surface import (
    _ctx,
    _editor,
    _governed_dispatch,
    _viewer,
)
from tv_app.interface.mcp import tool_bridge

PLANNER = (
    "tv_app.application.gpt_actions.dispatch_service."
    "PresentationCommandPlannerService"
)


def _suggest(message, host=None):
    dispatch, _, _ = _governed_dispatch()
    plan_result = {
        "operations": [{"op": "add_slide", "type": "data_chart"}],
        "slides": [{"kind": "chart"}],
    }
    with patch(
        f"{PLANNER}.plan", return_value=plan_result
    ), patch(
        f"{PLANNER}.to_suggest_payload",
        return_value={"operations": plan_result["operations"],
                      "slides": plan_result["slides"]},
    ):
        return dispatch.suggest_change(
            user=_editor(),
            message=message,
            host_context=host or {},
            authorization=None,
        )


def test_scenario_a_production_composes():
    out = _suggest(
        "crie um painel para acompanhar a eficiência da produção "
        "e destacar os principais problemas"
    )
    assert out["operations"], "proposta sem operações tipadas"
    assert out.get("designMethodology"), "sem advisory de metodologia"


def test_scenario_b_stock_composes():
    out = _suggest(
        "quero uma TV mostrando quais produtos precisam de maior "
        "atenção no estoque"
    )
    assert out["operations"]


def test_scenario_c_sales_composes():
    out = _suggest(
        "crie um painel para a equipe acompanhar as vendas em "
        "relação às metas"
    )
    assert out["operations"]


def test_scenario_d_quality_composes():
    out = _suggest(
        "monte uma apresentação mostrando os principais problemas "
        "de qualidade e como eles estão evoluindo"
    )
    assert out["operations"]


def test_scenario_e_executive_composes():
    out = _suggest(
        "crie uma apresentação executiva da situação geral "
        "das operações da empresa"
    )
    assert out["operations"]


def test_intent_materialization_routes_to_suggest():
    dispatch, _, _ = _governed_dispatch()
    with patch(
        f"{PLANNER}.plan", return_value={"operations": []}
    ), patch(
        f"{PLANNER}.to_suggest_payload", return_value={"operations": []}
    ):
        out = dispatch.semantic_analyze(
            user=_editor(),
            analysis="intent_materialization",
            parameters={"message": "crie um painel de vendas"},
            subject_refs={},
            authorization=None,
        )
    assert out["evidenceClass"] == "calculation"
    assert "operations" in out


def test_suggest_requires_write_permission():
    dispatch, _, _ = _governed_dispatch()
    import pytest

    with pytest.raises(PermissionError):
        dispatch.suggest_change(
            user=_viewer(),
            message="crie um painel",
            host_context={},
            authorization=None,
        )

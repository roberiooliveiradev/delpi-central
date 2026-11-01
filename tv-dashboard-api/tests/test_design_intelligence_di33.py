"""DI-3.3 — binding plan on composition: route discovery classified
RESOLVED / NEEDS_SOURCE_SELECTION / NEEDS_CONTEXT — never fabricated."""
from __future__ import annotations

import test_vista_execute as tx


def _suggest(message, host=None):
    d, _, _ = tx._dispatch()
    return d.suggest_change(
        user=tx._user(),
        message=message,
        host_context=host or {"playlistId": "p1", "slideId": "s1"},
        authorization=None,
    )


def test_binding_plan_present_on_data_ops():
    out = _suggest(
        "crie um painel para acompanhar produtividade e problemas "
        "da fábrica"
    )
    bp = out.get("bindingPlan")
    assert bp is not None
    assert bp["dataBlockOps"] > 0
    assert bp["state"] in {
        "RESOLVED", "NEEDS_SOURCE_SELECTION", "NEEDS_CONTEXT",
    }


def test_ambiguous_sources_not_silently_picked():
    out = _suggest("quero acompanhar vendas e metas")
    bp = out.get("bindingPlan")
    assert bp["state"] == "NEEDS_SOURCE_SELECTION"
    total = sum(len(b["candidates"]) for b in bp["blocks"])
    assert total > 1


def test_ops_still_materialize_with_binding_plan():
    out = _suggest(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    assert out["status"] == "ready"
    assert out["ops"]
    assert out["bindingPlan"]


def test_no_data_ops_no_binding_plan():
    out = _suggest("adicione um título ao slide")
    # heading-only ops → sem blocos de dados → sem bindingPlan
    if out.get("ops") and not any(
        (o.get("block") or {}).get("type")
        in {"kpi_view", "chart_view", "data_kpi", "data_chart",
            "data_table", "canvas_table", "table_view"}
        for o in out["ops"]
    ):
        assert out.get("bindingPlan") is None

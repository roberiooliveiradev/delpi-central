"""DI-3.6.2 — semantic boundary (5S/Kaizen out of production unless
explicit) + intent coverage (explicit 5S composes)."""
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


def _blocks(message):
    return _suggest(message)["bindingPlan"]["blocks"]


def _ids(b):
    return {c["operationId"] for c in b["candidates"]}


PROD = "crie um painel para acompanhar produtividade e problemas da fábrica"


def test_5s_not_in_production_chart():
    chart = next(
        b for b in _blocks(PROD) if b["blockType"] == "chart_view"
    )
    ids = _ids(chart)
    assert "get_audit_5s_summary_series" not in ids
    assert "get_kaizen_savings_investment_series" not in ids
    assert "get_kaizen_summary_series" not in ids


def test_5s_not_dominating_production_table():
    table = next(
        b for b in _blocks(PROD) if b["blockType"] == "table_view"
    )
    ids = _ids(table)
    audit = [i for i in ids if "audit_5s" in i]
    assert len(audit) <= 1


def test_production_series_preserved():
    chart = next(
        b for b in _blocks(PROD) if b["blockType"] == "chart_view"
    )
    ids = _ids(chart)
    assert any(
        "production" in i or "eficiencia" in i or "oee" in i
        for i in ids
    )


def test_explicit_5s_composes():
    out = _suggest("crie um painel de auditorias 5S e não conformidades")
    assert out["status"] in {"proposal", "ready"}
    assert out["ops"], "5S explícito deve materializar ops"
    blocks = out["bindingPlan"]["blocks"]
    assert any(
        "audit_5s" in i or "nonconform" in i
        for b in blocks for i in _ids(b)
    )


def test_explicit_5s_audit_sources():
    out = _suggest("crie um painel de auditorias 5S e não conformidades")
    blocks = out["bindingPlan"]["blocks"]
    table = next(b for b in blocks if b["blockType"] in {
        "table_view", "data_table", "canvas_table",
    })
    assert any("audit" in i or "nonconform" in i for i in _ids(table))


def test_kaizen_explicit_keeps_kaizen():
    out = _suggest(
        "crie um painel de resultados das iniciativas Kaizen"
    )
    blocks = (out.get("bindingPlan") or {}).get("blocks") or []
    if blocks:
        ids = {i for b in blocks for i in _ids(b)}
        assert any("kaizen" in i for i in ids)


def test_sales_unchanged():
    out = _suggest("quero acompanhar vendas e metas")
    blocks = out["bindingPlan"]["blocks"]
    ids = {i for b in blocks for i in _ids(b)}
    assert any(
        "sales" in i or "billing" in i or "commercial" in i
        for i in ids
    )

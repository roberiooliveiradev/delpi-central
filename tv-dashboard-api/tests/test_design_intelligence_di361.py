"""DI-3.6.1 — business domain anchoring: purpose suffixes never
promote cross-domain sources over the business intent."""
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


def test_openapi_diff_not_promoted_to_production():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade e problemas "
        "da fábrica"
    )
    for b in blocks:
        ids = {c["operationId"] for c in b["candidates"]}
        assert "get_openapi_diff" not in ids


def test_commercial_series_not_in_production_chart():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    ids = {c["operationId"] for c in chart["candidates"]}
    assert "get_commercial_rol_series" not in ids
    assert "get_transformometro_savings_investment_series" not in ids


def test_production_oee_series_present():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    ids = {c["operationId"] for c in chart["candidates"]}
    assert any(
        "oee" in oid or "eficiencia" in oid or "efficiency" in oid
        or "production" in oid for oid in ids
    )


def test_sales_sources_stay_commercial():
    blocks = _blocks("quero acompanhar vendas e metas")
    for b in blocks:
        cats = {c.get("category") for c in b["candidates"]}
        assert "commercial" in cats or any(
            "billing" in c["operationId"]
            or "sales" in c["operationId"]
            for c in b["candidates"]
        )


def test_customer_avatar_still_excluded():
    blocks = _blocks("quero acompanhar vendas e metas")
    for b in blocks:
        ids = {c["operationId"] for c in b["candidates"]}
        assert "get_customer_avatar" not in ids


def test_states_preserved():
    blocks = _blocks("crie um painel de produtividade da fábrica")
    for b in blocks:
        assert b["state"] in {
            "RESOLVED", "NEEDS_SOURCE_SELECTION", "NEEDS_CONTEXT",
        }

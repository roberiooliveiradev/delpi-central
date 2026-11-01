"""DI-3.6 — semantic purpose matching per block + binding spec on
RESOLVED + relevance threshold."""
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


def test_chart_prefers_series_sources():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    ids = {c["operationId"] for c in chart["candidates"]}
    assert any(
        "series" in oid or "efficiency" in oid for oid in ids
    )


def test_table_prefers_list_sources():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    table = next(b for b in blocks if b["blockType"] == "table_view")
    ids = {c["operationId"] for c in table["candidates"]}
    assert any(
        "list" in oid or "detalhes" in oid or "retrabalhos" in oid
        or "inspecoes" in oid or "inspection" in oid
        or "pending" in oid or "incomplete" in oid
        or "supplies" in oid
        for oid in ids
    )


def test_candidates_bounded():
    blocks = _blocks("quero acompanhar vendas e metas")
    for b in blocks:
        assert len(b["candidates"]) <= 8


def test_sales_chart_excludes_avatar_noise():
    blocks = _blocks("quero acompanhar vendas e metas")
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    ids = {c["operationId"] for c in chart["candidates"]}
    assert "get_customer_avatar" not in ids


def test_states_still_typed():
    blocks = _blocks("crie um painel de produtividade")
    for b in blocks:
        assert b["state"] in {
            "RESOLVED", "NEEDS_SOURCE_SELECTION", "NEEDS_CONTEXT",
        }


def test_binding_spec_shape_when_resolved():
    blocks = _blocks("crie um painel de produtividade da fábrica")
    for b in blocks:
        if b["state"] == "RESOLVED":
            binding = b.get("binding")
            assert binding is not None
            assert binding.get("operationId")
            assert binding.get("displayMode")
            assert isinstance(binding.get("missingParams"), list)

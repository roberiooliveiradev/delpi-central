"""DI-3.5 — strict component–data contract compatibility.

`auto` nunca conta como evidência: scalar-only routes não podem
alimentar line_chart sem modo/transformação declarados; fallback
por domínio usa o catálogo canônico quando o ranking lexical é fraco.
"""
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


def test_scalar_only_not_eligible_for_line_chart():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    for c in chart["candidates"]:
        declared = set(c.get("allowedDisplayModes") or [])
        # scalar+auto sozinho não é evidência de série temporal
        assert "line_chart" in declared or (
            "auto" in declared
            and c.get("metaShape") in {"list", "paged_list"}
        )


def test_different_candidates_per_component():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    kpi = next(b for b in blocks if b["blockType"] == "kpi_view")
    chart_ids = {c["operationId"] for c in chart["candidates"]}
    kpi_ids = {c["operationId"] for c in kpi["candidates"]}
    # o conjunto do chart não é igual ao do kpi — contratos distintos
    assert chart_ids != kpi_ids
    assert chart_ids, "chart sem candidato compatível"


def test_chart_candidates_declare_line_or_series_shape():
    blocks = _blocks(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    for c in chart["candidates"]:
        declared = set(c.get("allowedDisplayModes") or [])
        assert "line_chart" in declared or (
            "auto" in declared
            and c.get("metaShape") in {"list", "paged_list"}
        )


def test_sales_chart_gets_series_sources():
    blocks = _blocks("quero acompanhar vendas e metas")
    chart = next(b for b in blocks if b["blockType"] == "chart_view")
    ids = {c["operationId"] for c in chart["candidates"]}
    assert any("series" in oid for oid in ids)


def test_document_export_still_excluded():
    blocks = _blocks("quero acompanhar vendas e metas")
    for b in blocks:
        for c in b["candidates"]:
            assert c.get("metaShape") != "document_export"


def test_blocks_still_state_typed():
    blocks = _blocks("crie um painel de produtividade da fábrica")
    for b in blocks:
        assert b["state"] in {
            "RESOLVED", "NEEDS_SOURCE_SELECTION", "NEEDS_CONTEXT",
        }

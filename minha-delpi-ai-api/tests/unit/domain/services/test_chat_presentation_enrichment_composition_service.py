"""Compõe visuais de enrichment no renderPlan do primary (wave-2 critic)."""

from app.domain.services.chat_presentation_enrichment_composition_service import (
    ChatPresentationEnrichmentCompositionService,
)


def _stock_primary_meta():
    return {
        "ok": True,
        "compositionRole": "primary",
        "path": "/products/10080001/stock",
        "preferredFormat": "table",
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
        },
        "renderPlan": {
            "version": 1,
            "layoutMode": "single",
            "segments": [
                {"kind": "markdown", "slot": "lead", "source": "assistantMessage"},
                {"kind": "table", "slot": "primary", "source": "tablePresentation"},
            ],
        },
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01"}],
        },
    }


def _sales_enrichment_meta():
    return {
        "ok": True,
        "compositionRole": "enrichment",
        "path": "/products/10080001/sales",
        "preferredFormat": "kpi",
        "presentationDecision": {"selected": "kpi", "layoutMode": "single"},
        "renderPlan": {
            "version": 1,
            "layoutMode": "single",
            "segments": [
                {"kind": "markdown", "slot": "lead", "source": "assistantMessage"},
                {"kind": "kpi", "slot": "primary", "source": "kpiPresentation"},
            ],
        },
        "kpiPresentation": {
            "type": "kpi",
            "title": "Indicador",
            "cards": [{"key": "documents", "label": "Documentos", "value": 67}],
        },
    }


def test_compose_merges_enrichment_kpi_into_primary_render_plan():
    primary = _stock_primary_meta()
    enrichment = _sales_enrichment_meta()
    tool_calls = [
        {"name": "execute_external_action", "metadata": primary},
        {"name": "execute_external_action", "metadata": enrichment},
    ]

    ChatPresentationEnrichmentCompositionService.compose_into_primary(tool_calls)

    kinds = [str(s.get("kind")) for s in primary["renderPlan"]["segments"]]
    assert "table" in kinds
    assert "kpi" in kinds
    assert primary["renderPlan"]["layoutMode"] == "stack"
    assert primary["presentationDecision"]["layoutMode"] == "stack"
    assert primary.get("kpiPresentation", {}).get("type") == "kpi"

    enrichment_kinds = [
        str(s.get("kind")) for s in enrichment["renderPlan"]["segments"]
    ]
    assert enrichment_kinds == ["markdown"]
    assert "kpi" not in enrichment_kinds


def test_compose_noop_without_enrichment():
    primary = _stock_primary_meta()
    tool_calls = [{"name": "execute_external_action", "metadata": primary}]
    plan_before = list(primary["renderPlan"]["segments"])

    ChatPresentationEnrichmentCompositionService.compose_into_primary(tool_calls)

    assert primary["renderPlan"]["segments"] == plan_before
    assert primary["renderPlan"]["layoutMode"] == "single"


def test_compose_skips_duplicate_visual_kind():
    primary = _stock_primary_meta()
    enrichment = _sales_enrichment_meta()
    enrichment["renderPlan"]["segments"] = [
        {"kind": "table", "slot": "primary", "source": "tablePresentation"},
    ]
    enrichment["tablePresentation"] = {
        "type": "table",
        "title": "Outra",
        "columns": [{"key": "a", "label": "A"}],
        "rows": [{"a": 1}],
    }
    tool_calls = [
        {"name": "execute_external_action", "metadata": primary},
        {"name": "execute_external_action", "metadata": enrichment},
    ]

    ChatPresentationEnrichmentCompositionService.compose_into_primary(tool_calls)

    table_segments = [
        s
        for s in primary["renderPlan"]["segments"]
        if str(s.get("kind")) == "table"
    ]
    assert len(table_segments) == 1

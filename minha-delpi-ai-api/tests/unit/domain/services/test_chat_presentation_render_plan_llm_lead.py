"""Regressão: estoque/tabela com llmProseDecoupled deve emitir lead assistantMessage."""

from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)


def test_single_view_table_with_llm_prose_decoupled_includes_assistant_message_lead():
    metadata = {
        "llmProseDecoupled": True,
        "dataOnlyPresentation": True,
        "proseDeliveryMode": "llm",
        "textPresentation": {"type": "markdown", "markdown": ""},
        "tablePresentation": {
            "type": "table",
            "title": "Estoque do produto",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01"}],
        },
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
            "proseSource": "llm",
            "insight": "A tabela lista os principais registros encontrados (4 linhas).",
        },
    }

    ChatPresentationRenderPlanService.build(metadata)
    plan = metadata.get("renderPlan") or {}
    segments = plan.get("segments") or []

    assert {"kind": "markdown", "slot": "lead", "source": "assistantMessage"} in segments
    assert any(
        segment.get("kind") == "table" and segment.get("slot") == "primary"
        for segment in segments
        if isinstance(segment, dict)
    )


def test_single_view_table_without_decouple_omits_empty_lead():
    metadata = {
        "llmProseDecoupled": False,
        "textPresentation": {"type": "markdown", "markdown": ""},
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01"}],
        },
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
        },
    }

    ChatPresentationRenderPlanService.build(metadata)
    segments = (metadata.get("renderPlan") or {}).get("segments") or []

    assert not any(
        segment.get("kind") == "markdown" and segment.get("slot") == "lead"
        for segment in segments
        if isinstance(segment, dict)
    )
    assert any(segment.get("kind") == "table" for segment in segments if isinstance(segment, dict))


def _assert_lead_then_primary(metadata: dict, primary_kind: str) -> None:
    ChatPresentationRenderPlanService.build(metadata)
    segments = [
        segment
        for segment in ((metadata.get("renderPlan") or {}).get("segments") or [])
        if isinstance(segment, dict)
    ]
    assert segments
    assert segments[0].get("kind") == "markdown"
    assert segments[0].get("slot") == "lead"
    assert segments[0].get("source") == "assistantMessage"
    primary = next(
        (
            segment
            for segment in segments
            if segment.get("slot") == "primary" or segment.get("kind") == primary_kind
        ),
        None,
    )
    assert primary is not None
    assert primary.get("kind") == primary_kind
    lead_idx = 0
    primary_idx = segments.index(primary)
    assert lead_idx < primary_idx


def test_decoupled_lead_before_tree_primary():
    _assert_lead_then_primary(
        {
            "llmProseDecoupled": True,
            "dataOnlyPresentation": True,
            "proseDeliveryMode": "llm",
            "treePresentation": {
                "type": "tree",
                "title": "Estrutura",
                "roots": [{"id": "1", "label": "PA"}],
            },
            "presentationDecision": {
                "selected": "tree",
                "layoutMode": "single",
                "proseSource": "llm",
            },
        },
        "tree",
    )


def test_decoupled_lead_before_kpi_primary():
    _assert_lead_then_primary(
        {
            "llmProseDecoupled": True,
            "dataOnlyPresentation": True,
            "proseDeliveryMode": "llm",
            "kpiPresentation": {
                "type": "kpi",
                "title": "Vendas",
                "items": [{"label": "Qtd", "value": 0}],
            },
            "presentationDecision": {
                "selected": "kpi",
                "layoutMode": "single",
                "proseSource": "llm",
            },
        },
        "kpi",
    )


def test_decoupled_lead_before_dashboard_primary():
    _assert_lead_then_primary(
        {
            "llmProseDecoupled": True,
            "dataOnlyPresentation": True,
            "proseDeliveryMode": "llm",
            "dashboardPresentation": {
                "type": "dashboard",
                "title": "Status fabril",
                "panels": [],
            },
            "presentationDecision": {
                "selected": "dashboard",
                "layoutMode": "single",
                "proseSource": "llm",
            },
        },
        "dashboard",
    )


def test_decoupled_table_lead_order_strict():
    metadata = {
        "llmProseDecoupled": True,
        "dataOnlyPresentation": True,
        "proseDeliveryMode": "llm",
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01"}],
        },
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
            "proseSource": "llm",
        },
    }
    _assert_lead_then_primary(metadata, "table")

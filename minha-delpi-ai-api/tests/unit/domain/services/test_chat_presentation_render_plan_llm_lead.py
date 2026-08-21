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

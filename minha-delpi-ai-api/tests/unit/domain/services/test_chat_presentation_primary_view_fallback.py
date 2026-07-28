from app.domain.services.chat_presentation_primary_view_service import (
    ChatPresentationPrimaryViewService,
)
from app.domain.services.chat_presentation_render_pipeline_service import (
    ChatPresentationRenderPipelineService,
)


def test_explicit_chart_falls_back_when_chart_slot_empty():
    metadata = {
        "explicitSessionFormat": "chart",
        "preferredFormat": "chart",
        "presentationDecision": {
            "selected": "chart",
            "fallback": "table",
            "layoutMode": "single",
            "availableViews": ["text", "table", "chart"],
            "reason": "formato solicitado pelo usuário",
        },
        "tablePresentation": {
            "type": "table",
            "title": "Lista",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": "1"}],
        },
        "chartPresentation": {"type": "chart", "title": "Série", "data": []},
        "textPresentation": {"markdown": "Resumo"},
    }

    ChatPresentationPrimaryViewService.sync_render_contract_for_explicit_session(metadata)

    decision = metadata["presentationDecision"]

    assert decision["selected"] == "table"
    assert "indisponível" in str(decision.get("reason") or "").lower()
    assert metadata.get("explicitSessionFormat") == "chart"


def test_explicit_tree_falls_back_when_tree_missing():
    metadata = {
        "explicitSessionFormat": "tree",
        "presentationDecision": {
            "selected": "tree",
            "fallback": "table",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
        },
        "tablePresentation": {
            "type": "table",
            "title": "Lista",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": "1"}],
        },
    }

    ChatPresentationPrimaryViewService.sync_render_contract_for_explicit_session(metadata)

    assert metadata["presentationDecision"]["selected"] == "table"


def test_finalize_render_plan_uses_fallback_selected_not_empty_chart():
    metadata = {
        "explicitSessionFormat": "chart",
        "presentationDecision": {
            "selected": "chart",
            "fallback": "table",
            "layoutMode": "single",
            "availableViews": ["table", "chart"],
        },
        "tablePresentation": {
            "type": "table",
            "title": "Lista",
            "columns": [{"key": "x", "label": "X"}],
            "rows": [{"x": 1}],
        },
        "chartPresentation": {"type": "chart", "title": "Vazio", "data": []},
    }

    ChatPresentationRenderPipelineService.finalize(metadata)

    kinds = {
        str(segment.get("kind") or "").strip().lower()
        for segment in metadata["renderPlan"]["segments"]
    }

    assert "chart" not in kinds
    assert "table" in kinds

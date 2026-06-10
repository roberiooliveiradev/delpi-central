from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)


def test_enrich_metadata_honors_explicit_session_format_without_user_preference_param():
    metadata = {
        "path": "/products/10080001/stock",
        "explicitSessionFormat": "table",
        "preferredFormat": "table",
        "presentation": {
            "type": "table",
            "title": "Estoque",
            "columns": [{"key": "branch", "label": "Filial"}],
            "rows": [{"branch": "01", "current_quantity": 10}],
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estoque\n\n- Filial 01",
        },
        "availableFormats": ["text", "table", "chart"],
    }

    ChatPresentationDecisionService.enrich_metadata(
        metadata,
        user_message="estoque do produto 10080001",
        user_preference=None,
    )

    decision = metadata["presentationDecision"]

    assert decision["selected"] == "table"
    assert decision["layoutMode"] == "single"


def test_integrated_stack_does_not_override_explicit_text_preference():
    metadata = {
        "path": "/products/90269002/factory-status",
        "apiDelpiResponseMeta": {"entity": "product_factory_status"},
        "explicitSessionFormat": "text",
        "textPresentation": {"type": "markdown", "markdown": "### Status\n\nResumo."},
        "tablePresentations": [{"type": "table", "title": "Panorama", "rows": []}],
        "availableFormats": ["text", "table", "dashboard"],
    }

    ChatPresentationDecisionService.enrich_metadata(
        metadata,
        user_message="visão integrada do status fabril do produto 90269002",
        user_preference="text",
    )

    decision = metadata["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"

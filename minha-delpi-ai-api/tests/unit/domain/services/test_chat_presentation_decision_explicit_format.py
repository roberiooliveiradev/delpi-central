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

from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)


def test_tree_preference_without_hierarchy_falls_back_to_text_for_overview():
    rows = [{"campo": "Código", "valor": "90260114"}]

    decision = ChatPresentationDecisionService.decide(
        rows=rows,
        user_message="me fale do produto 90260114",
        user_preference="tree",
        available_formats=["text", "table"],
        text_presentation={"type": "markdown", "markdown": "Visão do produto"},
    )

    assert decision["selected"] == "text"
    assert "indisponível" in decision["reason"] or "narrativa" in decision["reason"]


def test_operational_intent_prefers_text_for_product_overview():
    decision = ChatPresentationDecisionService.decide(
        user_message="me fale do produto 90260114",
        text_presentation={"type": "markdown", "markdown": "Visão"},
        table_presentation={
            "type": "table",
            "rows": [{"campo": "Código", "valor": "90260114"}],
        },
        available_formats=["text", "table"],
    )

    assert decision["selected"] == "text"

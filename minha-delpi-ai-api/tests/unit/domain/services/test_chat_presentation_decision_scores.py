from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)


def test_compute_scores_prefers_chart_for_categorical_shape():
    scores = ChatPresentationDecisionService.compute_scores(
        data_shape={
            "rows": 5,
            "hasCategory": True,
            "hasNumeric": True,
            "recommended": "horizontal_bar",
        },
        available_views=["text", "table", "chart"],
        user_message="ranking de saldo por filial",
    )

    assert scores["chart"] >= scores["table"]
    assert scores["chart"] >= 50


def test_compute_scores_prefers_tree_for_hierarchy():
    scores = ChatPresentationDecisionService.compute_scores(
        data_shape={
            "rows": 12,
            "hasHierarchy": True,
            "recommended": "tree",
        },
        available_views=["text", "table", "tree"],
    )

    assert scores["tree"] >= 50


def test_attach_scores_and_reading_layers_from_data_answer():
    decision = {
        "selected": "text",
        "availableViews": ["text", "table"],
        "dataShape": {"rows": 3, "hasNumeric": True},
    }
    metadata = {
        "dataAnswer": {
            "summary": {
                "answer": "Saldo confortável em duas filiais.",
                "nextAction": "Conferir posição com disponível negativo.",
            }
        },
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"filial": "01", "saldo": 100},
                {"filial": "02", "saldo": 50},
            ],
        },
    }

    ChatPresentationDecisionService._attach_scores_and_reading_layers(
        decision,
        metadata=metadata,
        table_rows=metadata["tablePresentation"]["rows"],
        user_message="estoque do produto",
    )

    assert decision.get("scores")
    assert decision.get("readingLayers")
    assert decision.get("purpose") == "Conferir posição com disponível negativo."
    assert "Saldo confortável" in str(decision.get("message") or "")

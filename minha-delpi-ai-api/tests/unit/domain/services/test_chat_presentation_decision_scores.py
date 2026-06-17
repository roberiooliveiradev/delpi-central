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

    ChatPresentationDecisionService._ensure_purpose(
        decision,
        metadata=metadata,
        user_message="estoque do produto",
    )

    assert decision.get("scores")
    assert decision.get("readingLayers")
    assert decision.get("purpose") == "estoque do produto"
    assert "Conferir posição" not in str(decision.get("purpose") or "")
    assert "Saldo confortável" in str(decision.get("message") or "")


def test_compute_scores_prefers_table_for_listing_question():
    scores = ChatPresentationDecisionService.compute_scores(
        data_shape={
            "rows": 50,
            "hasCategory": True,
            "hasNumeric": True,
            "recommended": "horizontal_bar",
        },
        available_views=["text", "table", "chart"],
        user_message="quais os produtos programados para produzir hoje",
    )

    assert scores["table"] > scores["chart"]


def test_apply_automatic_score_selection_keeps_table_for_playbook_report():
    decision = {
        "selected": "table",
        "fallback": "text",
        "layoutMode": "single",
        "availableViews": ["text", "table", "horizontal_bar", "chart"],
        "scores": {
            "text": 25,
            "table": 35,
            "chart": 85,
        },
        "dataShape": {
            "rows": 50,
            "hasCategory": True,
            "hasNumeric": True,
            "recommended": "horizontal_bar",
        },
    }
    metadata = {
        "path": "/production/schedule/today",
        "apiDelpiResponseMeta": {"entity": "production_schedule_today"},
        "tablePresentation": {
            "type": "table",
            "rows": [{"production_order": "OP-1", "product_code": "70260010"}],
        },
        "chartPresentation": {"type": "chart", "chartType": "heatmap", "data": []},
    }

    ChatPresentationDecisionService._apply_automatic_score_selection(
        decision,
        metadata=metadata,
        effective_preference=None,
        user_message="quais os produtos programados para produzir hoje",
        path="/production/schedule/today",
        entity="production_schedule_today",
    )

    assert decision["selected"] == "table"


def test_decide_prefers_table_for_production_schedule_with_chart_payload():
    rows = [
        {
            "production_order": "000001",
            "product_code": "70260010",
            "description": "CHICOTE BUHLER",
            "planned_quantity": 0,
        }
    ] * 50

    decision = ChatPresentationDecisionService.decide(
        rows=rows,
        user_message="quais os produtos programados para produzir hoje",
        table_presentation={"type": "table", "rows": rows},
        chart_presentation={"type": "chart", "chartType": "heatmap", "data": []},
        path="/production/schedule/today",
        metadata={
            "path": "/production/schedule/today",
            "apiDelpiResponseMeta": {"entity": "production_schedule_today"},
        },
    )

    assert decision["selected"] == "table"


def test_apply_automatic_score_selection_picks_chart_for_categorical_rows():
    decision = {
        "selected": "table",
        "fallback": "text",
        "layoutMode": "single",
        "availableViews": ["text", "table", "horizontal_bar", "chart"],
        "scores": {
            "text": 25,
            "table": 35,
            "chart": 85,
        },
        "dataShape": {
            "rows": 6,
            "hasCategory": True,
            "hasNumeric": True,
            "recommended": "horizontal_bar",
        },
    }
    metadata = {
        "tablePresentation": {"type": "table", "rows": [{"filial": "01", "saldo": 1}]},
        "chartPresentation": {"type": "chart", "chartType": "horizontal_bar", "data": []},
    }

    ChatPresentationDecisionService._apply_automatic_score_selection(
        decision,
        metadata=metadata,
        effective_preference=None,
        user_message="ranking de saldo por filial",
        path="/products/10070014/guide",
        entity="product_guide",
    )

    assert decision["selected"] == "horizontal_bar"
    assert decision["reason"]


def test_apply_automatic_score_selection_skips_with_explicit_preference():
    decision = {
        "selected": "table",
        "fallback": "text",
        "layoutMode": "single",
        "availableViews": ["text", "table", "chart"],
        "scores": {"text": 10, "table": 20, "chart": 95},
    }

    ChatPresentationDecisionService._apply_automatic_score_selection(
        decision,
        metadata={},
        effective_preference="table",
        user_message="",
        path="/products/90269001/stock",
        entity="product_stock",
    )

    assert decision["selected"] == "table"


def test_ensure_purpose_uses_user_message_when_data_answer_missing():
    decision = {"selected": "table"}
    metadata = {
        "tablePresentation": {
            "type": "table",
            "rows": [{"filial": "01", "saldo": 1}],
        }
    }

    ChatPresentationDecisionService._ensure_purpose(
        decision,
        metadata=metadata,
        user_message="estoque do produto 90269001",
    )

    assert decision["purpose"] == "estoque do produto 90269001"

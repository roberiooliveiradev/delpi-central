from app.domain.services.chat_presentation_recommendation_service import (
    ChatPresentationRecommendationService,
)
from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)


def test_recommends_line_chart_when_table_has_dates():
    decision = {
        "selected": "table",
        "availableViews": ["table", "line_chart", "chart"],
        "dataShape": {
            "rows": 4,
            "hasDate": True,
            "hasNumeric": True,
            "categoryCardinality": 4,
        },
    }

    rows = [
        {"month": "jan/2026", "value": 10},
        {"month": "fev/2026", "value": 12},
        {"month": "mar/2026", "value": 15},
        {"month": "abr/2026", "value": 11},
    ]

    recommendations = ChatPresentationRecommendationService.build(
        decision=decision,
        metadata={"tablePresentation": {"type": "table", "rows": rows, "columns": []}},
    )

    views = {item["view"] for item in recommendations}

    assert "line_chart" in views


def test_recommends_horizontal_bar_for_efficiency_on_table():
    decision = {
        "selected": "table",
        "availableViews": ["table", "horizontal_bar", "chart"],
        "dataShape": {
            "rows": 10,
            "hasNumeric": True,
            "categoryCardinality": 10,
        },
    }

    recommendations = ChatPresentationRecommendationService.build(
        decision=decision,
        user_message="qual a eficiencia fabril de hoje?",
        metadata={
            "tablePresentation": {
                "type": "table",
                "rows": [{"nome": f"Op {index}", "eficiencia_percentual": 80 + index} for index in range(10)],
                "columns": [],
            }
        },
    )

    assert any(item["view"] == "horizontal_bar" for item in recommendations)


def test_recommendations_become_interactivity_chips():
    metadata = {
        "ok": True,
        "presentation": {"type": "table"},
        "presentationDecision": {
            "selected": "table",
            "availableViews": ["table", "line_chart"],
            "recommendations": [
                {
                    "view": "line_chart",
                    "label": "Ver em linha",
                    "query": "mostre em linha",
                    "reason": "série temporal",
                }
            ],
        },
    }

    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [{"name": "x", "metadata": metadata}]
    )

    assert any(item["label"] == "Ver em linha" for item in suggestions)

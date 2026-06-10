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


def test_prune_for_selected_removes_matching_view():
    decision = {
        "selected": "table",
        "recommendations": [
            {
                "view": "table",
                "label": "Ver como tabela",
                "query": "mostre em tabela",
                "reason": "detalhes tabulares",
            },
            {
                "view": "chart",
                "label": "Ver como gráfico",
                "query": "mostre em gráfico",
            },
        ],
    }

    ChatPresentationRecommendationService.prune_for_selected(decision)

    assert decision["recommendations"] == [
        {
            "view": "chart",
            "label": "Ver como gráfico",
            "query": "mostre em gráfico",
        }
    ]


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
                "rows": [
                    {"nome": f"Op {index}", "eficiencia_percentual": 80 + index}
                    for index in range(10)
                ],
                "columns": [],
            }
        },
    )

    assert any(item["view"] == "horizontal_bar" for item in recommendations)


def test_entity_family_recommends_table_when_text_selected_for_stock():
    decision = {
        "selected": "text",
        "availableViews": ["text", "table", "chart"],
        "presentationProfileKey": "stock",
        "dataShape": {"rows": 3},
    }

    recommendations = ChatPresentationRecommendationService.build(decision=decision)

    assert any(item["view"] == "table" for item in recommendations)


def test_entity_family_recommends_chart_for_playbook_report_with_numeric_shape():
    decision = {
        "selected": "table",
        "availableViews": ["text", "table", "chart"],
        "presentationProfileKey": "playbook_report",
        "dataShape": {"rows": 5, "hasNumeric": True},
    }

    recommendations = ChatPresentationRecommendationService.build(decision=decision)

    assert any(item["view"] == "chart" for item in recommendations)


def test_kpi_entity_family_recommends_chart_for_series_with_dates():
    decision = {
        "selected": "kpi",
        "availableViews": ["text", "kpi", "line_chart", "chart", "table"],
        "presentationProfileKey": "kpi_series",
        "dataShape": {"rows": 4, "hasDate": True, "hasNumeric": True},
    }

    recommendations = ChatPresentationRecommendationService.build(decision=decision)

    views = {item["view"] for item in recommendations}

    assert "line_chart" in views or "chart" in views
    assert "table" in views


def test_kpi_entity_family_recommends_kpi_when_text_selected():
    decision = {
        "selected": "text",
        "availableViews": ["text", "kpi", "table", "chart"],
        "presentationProfileKey": "kpi_snapshot",
    }

    recommendations = ChatPresentationRecommendationService.build(decision=decision)

    assert any(item["view"] == "kpi" for item in recommendations)


def test_kpi_series_chart_selected_recommends_table_and_text():
    decision = {
        "selected": "line_chart",
        "availableViews": ["text", "table", "chart", "line_chart"],
        "presentationProfileKey": "kpi_snapshot",
        "dataShape": {"rows": 2, "hasDate": True, "hasNumeric": True},
    }

    recommendations = ChatPresentationRecommendationService.build(decision=decision)

    views = {item["view"] for item in recommendations}

    assert "table" in views
    assert "text" in views


def test_kpi_profile_extra_chips_from_interactivity():
    metadata = {
        "ok": True,
        "path": "/commercial/closing-rate",
        "entity": "sales_conversion_rate",
        "presentation": {"type": "kpi", "title": "Taxa de Conversão", "cards": []},
        "presentationDecision": {
            "selected": "kpi",
            "availableViews": ["text", "kpi", "line_chart", "chart", "table"],
            "presentationProfileKey": "kpi_series",
            "dataShape": {"rows": 3, "hasDate": True, "hasNumeric": True},
        },
    }

    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [{"name": "execute_external_action", "metadata": metadata}]
    )

    labels = [item["label"] for item in suggestions]

    assert "Ver em linha" in labels
    assert "Exportar CSV" in labels


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


def test_profile_view_chips_respect_available_views_and_profile_order():
    metadata = {
        "ok": True,
        "path": "/products/10080001/stock",
        "entity": "product_stock",
        "presentation": {"type": "text"},
        "presentationDecision": {
            "selected": "text",
            "availableViews": ["text", "table", "chart"],
            "presentationProfileKey": "stock",
        },
    }

    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [{"name": "execute_external_action", "metadata": metadata}]
    )

    labels = [item["label"] for item in suggestions]

    assert "Ver como tabela" in labels
    assert "Ver em gráfico" in labels
    assert "Só com saldo" in labels

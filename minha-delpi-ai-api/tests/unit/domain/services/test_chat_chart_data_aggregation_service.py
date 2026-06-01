from app.domain.services.chat_chart_data_aggregation_service import (
    ChatChartDataAggregationService,
)


def test_aggregate_eficiencia_by_filial_weighted():
    rows = [
        {"filial": "01", "eficiencia_percentual": 100.0, "tempo_real_horas": 1.0},
        {"filial": "01", "eficiencia_percentual": 200.0, "tempo_real_horas": 3.0},
        {"filial": "02", "eficiencia_percentual": 50.0, "tempo_real_horas": 2.0},
    ]

    aggregated = ChatChartDataAggregationService.aggregate_by_category(
        rows,
        "filial",
        ["eficiencia_percentual"],
    )

    assert len(aggregated) == 2
    by_filial = {row["filial"]: row["eficiencia_percentual"] for row in aggregated}

    assert by_filial["01"] == 175.0
    assert by_filial["02"] == 50.0


def test_apply_to_chart_presentation_collapses_duplicate_categories():
    presentation = {
        "type": "chart",
        "chartType": "bar",
        "data": [
            {"filial": "02", "eficiencia_percentual": 147.87},
            {"filial": "02", "eficiencia_percentual": 54.45},
            {"filial": "01", "eficiencia_percentual": 480.0},
        ],
        "config": {
            "xAxis": "filial",
            "yAxis": ["eficiencia_percentual"],
        },
    }

    ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

    assert len(presentation["data"]) == 2

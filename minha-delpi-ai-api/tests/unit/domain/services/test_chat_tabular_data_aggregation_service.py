from app.domain.services.chat_tabular_data_aggregation_service import (
    ChatTabularDataAggregationService,
)


def test_aggregate_ranking_sums_by_unit():
    rows = [
        {"item_code": "1", "unit": "PC", "real_consumption_qty": 100.0},
        {"item_code": "2", "unit": "PC", "real_consumption_qty": 50.0},
        {"item_code": "3", "unit": "KG", "real_consumption_qty": 20.0},
    ]

    aggregated = ChatTabularDataAggregationService.aggregate_ranking(
        rows,
        category_field="unit",
        metric_fields=["real_consumption_qty"],
    )

    assert len(aggregated) == 2
    assert aggregated[0]["unit"] == "PC"
    assert aggregated[0]["real_consumption_qty"] == 150.0

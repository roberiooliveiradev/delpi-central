from tv_app.infrastructure.gateways.delpi_operational_gateway import _build_query_params


def test_date_range_strategy_forwards_extra_filters():
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "defaultParams": {"periodDays": 30},
        },
        {
            "periodDays": 14,
            "branch": "01",
            "customer_segment": "weg",
        },
    )
    assert query["branch"] == "01"
    assert query["customer_segment"] == "weg"
    assert "start_date" in query
    assert "end_date" in query
    assert "periodDays" not in query

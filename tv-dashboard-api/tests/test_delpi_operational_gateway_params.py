from datetime import date

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


def test_direct_strategy_resolves_relative_preset_to_schema_keys():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "paramSchema": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
                "branch": {"type": "string"},
            },
        },
        {"dateRangePreset": "this_month", "branch": "02"},
    )
    assert query["date_start"] == today.replace(day=1).isoformat()
    assert query["date_end"] == today.isoformat()
    assert query["branch"] == "02"
    assert "dateRangePreset" not in query


def test_direct_strategy_last_n_days():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "paramSchema": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
            },
        },
        {"dateRangePreset": "last_n_days", "periodDays": 10},
    )
    assert query["date_end"] == today.isoformat()
    assert query["date_start"] == (today.fromordinal(today.toordinal() - 9)).isoformat()

from datetime import date

from tv_app.infrastructure.gateways.delpi_operational_gateway import _build_query_params


def test_date_range_strategy_forwards_extra_filters():
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
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
    assert "date_start" not in query


def test_date_range_strategy_uses_schema_date_start_end_for_ppm():
    """PPM migrado: catálogo emite start_date/end_date (UI pode ainda mandar date_start)."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "defaultParams": {"periodDays": 30},
            "paramSchema": {
                "branch": {"type": "string"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "product_prefix": {"type": "string"},
            },
        },
        {
            "branch": "01",
            "date_start": "2026-01-01",
            "date_end": "2026-07-13",
            "product_prefix": "90",
        },
    )
    assert query == {
        "start_date": "2026-01-01",
        "end_date": "2026-07-13",
        "branch": "01",
        "product_prefix": "90",
    }
    assert "date_start" not in query
    assert "date_end" not in query


def test_date_range_maps_ui_aliases_to_canonical_start_date():
    """UI/legado pode gravar date_start; rota OEE espera start_date."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "paramSchema": {
                "branch": {"type": "string"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
        },
        {
            "branch": "01",
            "date_start": "2026-01-01",
            "date_end": "2026-07-13",
        },
    )
    assert query["start_date"] == "2026-01-01"
    assert query["end_date"] == "2026-07-13"
    assert "date_start" not in query
    assert "date_end" not in query


def test_date_range_maps_start_date_aliases_to_date_start():
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["date_start", "date_end"],
            "paramSchema": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
            },
        },
        {
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
        },
    )
    assert query["date_start"] == "2026-02-01"
    assert query["date_end"] == "2026-02-28"
    assert "start_date" not in query


def test_date_range_strategy_period_days_fallback_honors_schema_keys():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["date_start", "date_end"],
            "defaultParams": {"periodDays": 7},
            "paramSchema": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
            },
        },
        {"periodDays": 7},
    )
    assert query["date_end"] == today.isoformat()
    assert query["date_start"] == (today.fromordinal(today.toordinal() - 6)).isoformat()
    assert "start_date" not in query


def test_date_range_keys_on_route_without_schema_dates():
    """Catálogo legado: strategy date_range + dateRangeKeys, sem datas no schema."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["date_start", "date_end"],
            "defaultParams": {"periodDays": 30},
            "paramSchema": {"branch": {"type": "string"}, "periodDays": {"type": "integer"}},
        },
        {"branch": "02", "periodDays": 10},
    )
    assert "date_start" in query
    assert "date_end" in query
    assert "start_date" not in query
    assert query["branch"] == "02"


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
    assert "start_date" not in query


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


def test_direct_strategy_strips_date_aliases():
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "paramSchema": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
                "branch": {"type": "string"},
            },
        },
        {
            "date_start": "2026-03-01",
            "date_end": "2026-03-31",
            "start_date": "2099-01-01",
            "end_date": "2099-12-31",
            "branch": "01",
        },
    )
    assert query["date_start"] == "2026-03-01"
    assert query["date_end"] == "2026-03-31"
    assert "start_date" not in query
    assert "end_date" not in query


def test_date_range_keeps_api_granularity_untouched():
    """Granularidade da rota é preservada — nada de reagrupar dias em faixas."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "branch": {"type": "string"},
            },
            "fixedQueryParams": {"granularity": "day"},
        },
        {"start_date": "2026-01-01", "end_date": "2026-07-16"},
    )
    assert query["granularity"] == "day"
    assert query["start_date"] == "2026-01-01"
    assert query["end_date"] == "2026-07-16"


def test_date_range_strategy_respects_partial_end_date():
    """Só end_date do filtro — não recalcular fim=hoje."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "periodDays": {"type": "integer"},
            },
            "defaultParams": {"periodDays": 7},
        },
        {"end_date": "2026-07-10"},
    )
    assert query["end_date"] == "2026-07-10"
    assert query["start_date"] == "2026-07-04"


def test_date_range_omits_dates_when_no_period_without_open_ended_flag():
    """Sem datas e sem periodDays → omite o par (não depende de openEndedDateRange)."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "branch": {"type": "string"},
            },
        },
        {"branch": "01"},
    )
    assert "start_date" not in query
    assert "end_date" not in query
    assert query["branch"] == "01"


def test_open_ended_date_range_omits_dates_when_custom_empty():
    """Personalizado sem datas → não injeta últimos N dias."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "openEndedDateRange": True,
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "granularity": {"type": "string", "default": "month"},
                "filial_id": {"type": "string"},
            },
        },
        {"dateRangePreset": "custom", "granularity": "month", "filial_id": "01"},
    )
    assert "start_date" not in query
    assert "end_date" not in query
    assert query["granularity"] == "month"
    assert query["filial_id"] == "01"


def test_open_ended_partial_start_date_omits_invented_end():
    """openEnded + só start_date → envia só início (sem janela de 7 dias)."""
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "openEndedDateRange": True,
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "granularity": {"type": "string"},
            },
        },
        {"dateRangePreset": "custom", "start_date": "2025-06-01", "granularity": "month"},
    )
    assert query["start_date"] == "2025-06-01"
    assert "end_date" not in query
    assert query["granularity"] == "month"


def test_open_ended_partial_end_date_omits_invented_start():
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "openEndedDateRange": True,
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
        },
        {"dateRangePreset": "custom", "end_date": "2025-12-31"},
    )
    assert query["end_date"] == "2025-12-31"
    assert "start_date" not in query


def test_open_ended_still_honors_explicit_period_days():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "openEndedDateRange": True,
            "paramSchema": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
        },
        {"periodDays": 14},
    )
    assert query["end_date"] == today.isoformat()
    assert query["start_date"] == (today.fromordinal(today.toordinal() - 13)).isoformat()


def test_resolve_route_path_substitutes_and_requires_path_params():
    from tv_app.infrastructure.gateways.delpi_operational_gateway import (
        path_param_names,
        resolve_route_path,
        _strip_path_params_from_query,
    )

    path = "/production/oee/appointments/{appointment_id}"
    assert path_param_names(path) == ["appointment_id"]
    assert (
        resolve_route_path(path, {"appointment_id": 42, "branch": "01"})
        == "/production/oee/appointments/42"
    )
    try:
        resolve_route_path(path, {"branch": "01"})
        raise AssertionError("expected missing path param")
    except ValueError as exc:
        assert "appointment_id" in str(exc)

    query = _strip_path_params_from_query(
        {"appointment_id": "42", "branch": "01"},
        path=path,
    )
    assert query == {"branch": "01"}


def test_filter_query_drops_path_params_marked_in_schema():
    from tv_app.infrastructure.gateways.delpi_operational_gateway import _filter_query_to_route_schema

    filtered = _filter_query_to_route_schema(
        {"appointment_id": "9", "branch": "01"},
        schema={
            "appointment_id": {"type": "integer", "in": "path", "optional": False},
            "branch": {"type": "string", "optional": True},
        },
        fixed=None,
    )
    assert filtered == {"branch": "01"}


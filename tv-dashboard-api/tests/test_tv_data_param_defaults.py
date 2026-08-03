from datetime import date

from tv_app.application.services.data.tv_data_param_defaults_service import apply_catalog_param_defaults
from tv_app.application.services.data.tv_data_param_validation_service import validate_params_against_schema
from tv_app.infrastructure.gateways.delpi_operational_gateway import _build_query_params



def test_apply_defaults_never_injects_period_days():
    """Sem datas/preset → não inventa periodDays (histórico completo)."""
    route = {
        "paramSchema": {
            "start_date": {"type": "string", "optional": True},
            "end_date": {"type": "string", "optional": True},
            "periodDays": {"type": "integer", "optional": True, "default": 30},
        },
        "dateRangeKeys": ["start_date", "end_date"],
        "defaultParams": {"periodDays": 30},
    }
    merged = apply_catalog_param_defaults({}, route)
    assert "periodDays" not in merged
    assert "start_date" not in merged
    assert "end_date" not in merged


def test_apply_defaults_skips_period_days_for_open_ended_route():
    route = {
        "openEndedDateRange": True,
        "paramSchema": {
            "start_date": {"type": "string", "optional": True},
            "end_date": {"type": "string", "optional": True},
        },
        "dateRangeKeys": ["start_date", "end_date"],
    }
    merged = apply_catalog_param_defaults({}, route)
    assert "periodDays" not in merged
    assert "start_date" not in merged
    assert "end_date" not in merged


def test_apply_defaults_fills_required_branch_and_schema_default():
    route = {
        "defaultParams": {"periodDays": 30},
        "paramSchema": {
            "branch": {"type": "string", "optional": False},
            "granularity": {"type": "string", "optional": False, "default": "day"},
            "start_date": {"type": "string", "optional": True},
            "end_date": {"type": "string", "optional": True},
        },
        "dateRangeKeys": ["start_date", "end_date"],
    }
    merged = apply_catalog_param_defaults({"date_start": "2026-01-01", "date_end": "2026-01-31"}, route)
    assert merged["branch"] == "01"
    assert merged["granularity"] == "day"
    assert "periodDays" not in merged
    assert merged["date_start"] == "2026-01-01"


def test_apply_defaults_uses_todas_when_branch_enum_includes_todas():
    route = {
        "paramSchema": {
            "branch": {
                "type": "string",
                "optional": False,
                "enum": ["all", "01", "02"],
            },
        },
    }
    merged = apply_catalog_param_defaults({}, route)
    assert merged["branch"] == "all"


def test_apply_defaults_never_reinjects_department_id():
    """Limpar departamento no IDD não volta para commercial (overlay/schema)."""
    route = {
        "paramSchema": {
            "department_id": {
                "type": "string",
                "optional": True,
                "enum": ["commercial", "quality"],
                "default": "commercial",
            }
        }
    }
    assert "department_id" not in apply_catalog_param_defaults({}, route)
    assert "department_id" not in apply_catalog_param_defaults({"department_id": ""}, route)


def test_apply_defaults_skips_optional_enum_select_defaults():
    route = {
        "paramSchema": {
            "status": {
                "type": "string",
                "optional": True,
                "enum": ["Todos", "Pontual"],
                "default": "Todos",
            },
            "granularity": {
                "type": "string",
                "optional": False,
                "enum": ["day", "week"],
                "default": "day",
            },
        }
    }
    merged = apply_catalog_param_defaults({}, route)
    assert "status" not in merged
    assert merged["granularity"] == "day"


def test_validate_cleared_department_stays_empty():
    schema = {
        "department_id": {
            "type": "string",
            "optional": True,
            "enum": ["commercial", "quality"],
            "default": "commercial",
            "label": "Departamento",
        }
    }
    assert validate_params_against_schema({}, schema) == {}
    assert validate_params_against_schema({"department_id": ""}, schema) == {}


def test_gateway_applies_defaults_and_drops_unknown_dates_for_branch_only_route():
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "paramSchema": {"branch": {"type": "string", "optional": False}},
        },
        {"date_start": "2026-01-01", "date_end": "2026-01-31"},
    )
    assert query == {"branch": "01"}


def test_gateway_fills_granularity_for_commercial_series_shape():
    query = _build_query_params(
        {
            "paramStrategy": "date_range",
            "dateRangeKeys": ["start_date", "end_date"],
            "defaultParams": {"periodDays": 30},
            "paramSchema": {
                "granularity": {"type": "string", "optional": False, "default": "day", "enum": ["day", "week"]},
                "start_date": {"type": "string", "optional": True},
                "end_date": {"type": "string", "optional": True},
            },
        },
        {"date_start": "2026-01-01", "date_end": "2026-01-31"},
    )
    assert query["granularity"] == "day"
    assert query["start_date"] == "2026-01-01"
    assert query["end_date"] == "2026-01-31"
    assert "date_start" not in query


def test_gateway_maps_smoke_dates_to_retrabalho_keys_and_filial():
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "dateRangeKeys": ["dataInicio", "dataFim"],
            "defaultParams": {"periodDays": 30},
            "paramSchema": {
                "filial": {"type": "string", "optional": False},
                "dataInicio": {"type": "string", "optional": True},
                "dataFim": {"type": "string", "optional": True},
            },
        },
        {"date_start": "2026-03-01", "date_end": "2026-03-31"},
    )
    assert query == {
        "filial": "01",
        "dataInicio": "2026-03-01",
        "dataFim": "2026-03-31",
    }


def test_validate_accepts_required_dates_via_date_range_preset():
    schema = {
        "branch": {"type": "string", "optional": False},
        "date_start": {"type": "string", "optional": False},
        "date_end": {"type": "string", "optional": False},
    }
    route = {"paramSchema": schema, "defaultParams": {"periodDays": 30}}
    normalized = validate_params_against_schema(
        {"dateRangePreset": "this_month"},
        schema,
        route=route,
    )
    assert normalized["branch"] == "01"
    assert "date_start" not in normalized


def test_gateway_scheduling_uses_sc_branch_default():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "path": "/scheduling/bookings",
            "paramSchema": {
                "branch": {"type": "string", "optional": False},
                "from": {"type": "string", "optional": False},
                "to": {"type": "string", "optional": False},
            },
        },
        {"dateRangePreset": "this_month"},
    )
    assert query["branch"] == "SC"
    assert query["from"] == today.replace(day=1).isoformat()
    assert query["to"] == today.isoformat()


def test_gateway_scheduling_from_to_with_branch_default():
    today = date.today()
    query = _build_query_params(
        {
            "paramStrategy": "direct",
            "paramSchema": {
                "branch": {"type": "string", "optional": False},
                "from": {"type": "string", "optional": False},
                "to": {"type": "string", "optional": False},
            },
        },
        {"dateRangePreset": "this_month"},
    )
    assert query["branch"] == "01"
    assert query["from"] == today.replace(day=1).isoformat()
    assert query["to"] == today.isoformat()

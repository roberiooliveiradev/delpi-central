from datetime import date

from tv_app.application.services.data.tv_data_param_defaults_service import apply_catalog_param_defaults
from tv_app.application.services.data.tv_data_param_validation_service import validate_params_against_schema
from tv_app.infrastructure.gateways.delpi_operational_gateway import _build_query_params


def test_apply_defaults_uses_route_default_params_for_optional_group_by():
    """Select opcional: defaultParams NÃO força o wire — «Não definido aqui» omite o param."""
    route = {
        "paramSchema": {
            "group_by": {
                "type": "string",
                "optional": True,
                "default": "customer",
                "enum": ["none", "customer", "branch"],
            },
            "granularity": {
                "type": "string",
                "optional": True,
                "default": "week",
                "enum": ["day", "week", "month", "year"],
            },
        },
        "defaultParams": {"group_by": "customer"},
    }
    merged = apply_catalog_param_defaults({}, route)
    assert "group_by" not in merged
    assert "granularity" not in merged
    merged_none = apply_catalog_param_defaults({"group_by": "none"}, route)
    assert merged_none["group_by"] == "none"
    merged_week = apply_catalog_param_defaults({"granularity": "week"}, route)
    assert merged_week["granularity"] == "week"


def test_gateway_omits_optional_enum_selects_when_unset():
    """«Não definido aqui» omite group_by/granularity; a api-delpi aplica Query default."""
    route = {
        "paramStrategy": "date_range",
        "dateRangeKeys": ["start_date", "end_date"],
        "openEndedDateRange": True,
        "defaultParams": {"group_by": "customer"},
        "paramSchema": {
            "group_by": {
                "type": "string",
                "optional": True,
                "default": "customer",
                "enum": ["none", "customer", "branch"],
            },
            "granularity": {
                "type": "string",
                "optional": True,
                "default": "week",
                "enum": ["day", "week", "month", "year"],
            },
            "start_date": {"type": "string", "optional": True},
            "end_date": {"type": "string", "optional": True},
        },
    }
    query = _build_query_params(route, {})
    assert "group_by" not in query
    assert "granularity" not in query

    query_set = _build_query_params(route, {"group_by": "none", "granularity": "month"})
    assert query_set["group_by"] == "none"
    assert query_set["granularity"] == "month"


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


def test_otd_rol_summary_optional_filters_omit_when_unset():
    """Summaries OTD/ROL: branch e carteira opcionais não entram no wire vazios."""
    from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService

    catalog = TvDataRouteCatalogService()
    for operation_id in ("get_sales_order_otd_summary", "get_commercial_rol_summary"):
        route = catalog.get_route(operation_id)
        assert route is not None, operation_id
        merged = apply_catalog_param_defaults({}, route)
        assert "branch" not in merged, operation_id
        assert "customer_codes" not in merged, operation_id
        query = _build_query_params(route, {"dateRangePreset": "this_month"})
        assert "branch" not in query, operation_id
        assert "customer_codes" not in query, operation_id
        assert "customer_names" not in query, operation_id


def test_apply_defaults_skips_all_optional_filters_not_only_enums():
    """Bool/int/sort opcionais também respeitam «Não definido aqui» (todas as rotas)."""
    route = {
        "defaultParams": {
            "page": 1,
            "page_size": 50,
            "only_positive": True,
            "sort": "stock_value_desc",
        },
        "paramSchema": {
            "only_positive": {"type": "boolean", "optional": True, "default": True},
            "page": {"type": "integer", "optional": True, "default": 1},
            "page_size": {"type": "integer", "optional": True, "default": 50},
            "sort": {
                "type": "string",
                "optional": True,
                "default": "stock_value_desc",
                "enum": ["stock_value_desc", "quantity_desc"],
            },
            "branch": {"type": "string", "optional": False},
        },
    }
    merged = apply_catalog_param_defaults({}, route)
    assert "only_positive" not in merged
    assert "page" not in merged
    assert "page_size" not in merged
    assert "sort" not in merged
    assert merged["branch"] == "01"

    merged_set = apply_catalog_param_defaults(
        {"sort": "quantity_desc", "only_positive": False},
        route,
    )
    assert merged_set["sort"] == "quantity_desc"
    assert merged_set["only_positive"] is False


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

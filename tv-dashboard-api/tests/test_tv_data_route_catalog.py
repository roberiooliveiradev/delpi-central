from tv_app.application.services.comunicado_data_params_service import merge_data_params, param_inherited_from_slide
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_catalog_lists_allowlist_routes():
    catalog = TvDataRouteCatalogService()
    routes = catalog.list_routes()
    assert len(routes) >= 200
    ids = {item["operationId"] for item in routes}
    assert "get_overall_equipment_effectiveness_pct" in ids
    assert "get_production_oee_series" in ids
    assert "get_production_otd_series" in ids
    assert "get_ppm_external_summary" in ids
    assert "get_supplies_stock_value" in ids
    assert "get_dashboard_department_idd" in ids
    assert "get_dashboard_department_idd_dashboard_department_idd_get" not in ids


def test_catalog_resolves_legacy_department_idd_operation_id():
    """Playlists salvas com operationId auto-FastAPI devem resolver no canônico."""
    from tv_app.application.services.tv_data_route_catalog_service import (
        normalize_data_binding_operation_id,
        resolve_canonical_operation_id,
    )

    legacy = "get_dashboard_department_idd_dashboard_department_idd_get"
    canonical = "get_dashboard_department_idd"
    assert resolve_canonical_operation_id(legacy) == canonical

    catalog = TvDataRouteCatalogService()
    route = catalog.get_route(legacy)
    assert route is not None
    assert route["operationId"] == canonical
    assert catalog.is_allowed(legacy)
    assert route["paramSchema"]["department_id"]["enum"]

    binding = normalize_data_binding_operation_id({"operationId": legacy, "params": {"department_id": "commercial"}})
    assert binding is not None
    assert binding["operationId"] == canonical


def test_catalog_sales_conversion_rate_has_filters_and_value_fields():
    catalog = TvDataRouteCatalogService()
    route = catalog.get_route("get_sales_conversion_rate")
    assert route is not None
    assert "sales_conversion_rate_pct" in (route.get("valueFields") or [])
    schema = route.get("paramSchema") or {}
    assert "periodDays" in schema
    assert "branch" in schema
    assert "customer_segment" in schema
    assert route.get("paramStrategy") == "date_range"


def test_merge_data_params_slide_overrides_playlist_block_overrides_slide():
    merged = merge_data_params(
        playlist_defaults={"branch": "01", "periodDays": 30},
        slide_filters={"branch": "02", "periodDays": 14},
        block_params={"periodDays": 7},
    )
    assert merged["branch"] == "02"
    assert merged["periodDays"] == 7


def test_merge_data_params_input_overrides_block_and_clears_preset():
    """Filtro interativo vence dateRangePreset/this_month da fonte."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"dateRangePreset": "this_month", "branch": "01"},
        input_overrides={"periodDays": 4},
    )
    assert merged["periodDays"] == 4
    assert merged["branch"] == "01"
    assert "dateRangePreset" not in merged


def test_merge_data_params_input_end_date_clears_preset_and_period_days():
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"dateRangePreset": "this_month", "periodDays": 30},
        input_overrides={"end_date": "2026-07-10"},
    )
    assert merged["end_date"] == "2026-07-10"
    assert "dateRangePreset" not in merged
    assert "periodDays" not in merged


def test_param_inherited_from_slide():
    assert param_inherited_from_slide(
        "branch",
        slide_filters={"branch": "01"},
        block_params={},
    )
    assert not param_inherited_from_slide(
        "branch",
        slide_filters={"branch": "01"},
        block_params={"branch": "02"},
    )

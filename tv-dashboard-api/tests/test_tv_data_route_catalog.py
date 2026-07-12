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

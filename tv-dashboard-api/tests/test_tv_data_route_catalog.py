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


def test_catalog_rejects_unknown_operation():
    catalog = TvDataRouteCatalogService()
    assert catalog.is_allowed("get_overall_equipment_effectiveness_pct") is True
    assert catalog.is_allowed("unknown_operation") is False


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

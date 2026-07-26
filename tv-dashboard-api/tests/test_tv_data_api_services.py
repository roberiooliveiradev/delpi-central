import pytest

from tv_app.application.services.data.tv_data_config_validation_service import TvDataConfigValidationService
from tv_app.application.services.data.tv_data_param_validation_service import (
    validate_data_binding,
    validate_params_against_schema,
)
from tv_app.application.services.data.tv_data_presentation_modes_service import (
    block_type_for_display_mode,
    suggested_display_modes,
    validate_display_mode,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def _oee_route() -> dict:
    return TvDataRouteCatalogService().get_route("get_overall_equipment_effectiveness_pct") or {}


def test_suggested_display_modes_from_shape():
    modes = suggested_display_modes(allowed_display_modes=None, meta_shape="paged_list")
    assert "table" in modes
    assert block_type_for_display_mode("table") == "data_table"


def test_validate_params_applies_default_when_empty():
    schema = {"granularity": {"type": "string", "optional": False, "default": "day"}}
    assert validate_params_against_schema({"granularity": ""}, schema) == {"granularity": "day"}


def test_validate_params_allows_internal_date_range_preset():
    """UI grava dateRangePreset; expand acontece só no gateway HTTP."""
    schema = {
        "date_start": {"type": "string", "optional": True},
        "date_end": {"type": "string", "optional": True},
        "status": {"type": "string", "optional": True, "default": "Todos"},
    }
    assert validate_params_against_schema(
        {"dateRangePreset": "this_month", "status": "Todos", "periodDays": 15},
        schema,
    ) == {"status": "Todos"}


def test_validate_params_strips_unknown_api_keys():
    """Save alinhado ao fetch: chaves fora do schema são ignoradas (hydrate também remove)."""
    assert validate_params_against_schema(
        {"hack": "1", "status": "Todos"},
        {"status": {"type": "string", "optional": True}},
    ) == {"status": "Todos"}


def test_validate_params_skips_required_when_fixed_query_params():
    schema = {"granularity": {"type": "string", "optional": False}}
    assert (
        validate_params_against_schema(
            {},
            schema,
            fixed_query_params={"granularity": "day"},
        )
        == {}
    )


def test_validate_data_binding_otd_series_without_granularity():
    route = TvDataRouteCatalogService().get_route("get_production_otd_series") or {}
    if not route:
        pytest.skip("Catálogo OTD série indisponível")
    validate_data_binding(
        {
            "operationId": route["operationId"],
            "params": {"periodDays": 30, "branch": "02"},
            "displayMode": "line_chart",
        },
        block_type="data_chart",
        route=route,
    )


def test_validate_data_binding_rejects_non_get():
    route = dict(_oee_route())
    route["httpMethod"] = "POST"
    with pytest.raises(ValueError, match="GET"):
        validate_data_binding(
            {"operationId": route.get("operationId"), "params": {}, "displayMode": "kpi"},
            block_type="data_kpi",
            route=route,
        )


def test_validate_config_detects_invalid_operation():
    svc = TvDataConfigValidationService()
    result = svc.validate(
        {
            "blocks": [
                {
                    "type": "data_kpi",
                    "dataBinding": {"operationId": "not_in_allowlist", "params": {}},
                }
            ]
        }
    )
    assert result["valid"] is False
    assert any("operationId" in issue.get("field", "") for issue in result["issues"])


def test_validate_config_accepts_oee_kpi_block():
    route = _oee_route()
    if not route:
        pytest.skip("Catálogo OEE indisponível")
    svc = TvDataConfigValidationService()
    result = svc.validate(
        {
            "blocks": [
                {
                    "type": "data_kpi",
                    "dataBinding": {
                        "operationId": route["operationId"],
                        "params": {"periodDays": 7},
                        "displayMode": "kpi",
                    },
                }
            ]
        }
    )
    assert result["valid"] is True


def test_enrich_route_includes_suggested_modes():
    route = _oee_route()
    if not route:
        pytest.skip("Catálogo OEE indisponível")
    enriched = TvDataConfigValidationService().enrich_route_for_api(route)
    assert enriched.get("suggestedDisplayModes")


def test_validate_display_mode_accepts_universal_modes_on_scalar_route():
    route = _oee_route()
    if not route:
        pytest.skip("Catálogo OEE indisponível")
    validate_display_mode("table", allowed_display_modes=route.get("allowedDisplayModes"))
    validate_display_mode("bar_chart", allowed_display_modes=route.get("allowedDisplayModes"))

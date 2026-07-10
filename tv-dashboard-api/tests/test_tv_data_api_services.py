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


def test_validate_params_rejects_unknown_key():
    schema = {"branch": {"type": "string", "optional": True}}
    with pytest.raises(ValueError, match="não permitido"):
        validate_params_against_schema({"branch": "01", "foo": "bar"}, schema)


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

from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)


def test_filter_parameters_to_schema_removes_unknown_keys():
    action = {
        "parametersSchema": [
            {"name": "code"},
            {"name": "reference_date"},
        ],
    }

    filtered = ExternalActionProductRouteCatalogService.filter_parameters_to_schema(
        action,
        {"code": "90269002", "limit": 10, "reference_date": "2026-06-18"},
    )

    assert filtered == {"code": "90269002", "reference_date": "2026-06-18"}
    assert "limit" not in filtered


def test_build_exclusive_catalog_parameters_does_not_inject_limit_without_schema():
    service = ExternalActionProductRouteCatalogService(repository=None)
    action = {
        "parametersSchema": [
            {"name": "view"},
        ],
    }

    parameters = service.build_exclusive_catalog_parameters(
        action,
        message="quais produtos tem mp exclusiva",
        normalized="quais produtos tem mp exclusiva",
    )

    assert "limit" not in parameters
    assert parameters.get("view") == "by_material"

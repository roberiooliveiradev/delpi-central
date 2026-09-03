from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_system_metadata_intent_service import (
    ChatSystemMetadataIntentService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_score_prefers_schema_path():
    schema_action = {"path": "/system/tables/{tableName}/schema", "method": "GET"}
    detail_action = {"path": "/system/tables/{tableName}", "method": "GET"}
    message = "mostre o schema da tabela SB1010"

    assert ChatSystemMetadataIntentService.score_action(
        message, schema_action
    ) > ChatSystemMetadataIntentService.score_action(message, detail_action)


def test_score_prefers_indexes_path():
    indexes_action = {"path": "/system/tables/{tableName}/indexes", "method": "GET"}
    detail_action = {"path": "/system/tables/{tableName}", "method": "GET"}
    message = "índices da tabela SB1"

    assert ChatSystemMetadataIntentService.score_action(
        message, indexes_action
    ) > ChatSystemMetadataIntentService.score_action(message, detail_action)


def test_registry_has_system_table_schema_and_indexes_routes():
    routes = {
        str(route.get("id") or ""): route
        for route in OperationalRouteRegistryService.routes()
    }

    assert "systemTableSchema" in routes
    assert "systemTableIndexes" in routes
    detail = routes["systemTableDetail"]
    excludes = detail.get("route", {}).get("excludePathMarkers") or []
    assert "/schema" in excludes
    assert "/indexes" in excludes

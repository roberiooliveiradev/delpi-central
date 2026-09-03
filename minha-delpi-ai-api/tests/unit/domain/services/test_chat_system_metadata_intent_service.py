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
    schema_route = routes["systemTableSchema"].get("route") or {}
    indexes_route = routes["systemTableIndexes"].get("route") or {}
    assert schema_route.get("pathSuffix") == "/schema"
    assert indexes_route.get("pathSuffix") == "/indexes"
    detail = routes["systemTableDetail"]
    excludes = detail.get("route", {}).get("excludePathMarkers") or []
    assert "/schema" in excludes
    assert "/indexes" in excludes


def test_extract_table_name_from_indexes_without_tabela_word():
    assert (
        ChatSystemMetadataIntentService.extract_table_name("quais indexes da SB1010?")
        == "SB1010"
    )


def test_looks_like_question_for_indexes_without_tabela_word():
    normalized = "quais indexes da sb1010?"
    assert ChatSystemMetadataIntentService.looks_like_question(normalized)
    assert ChatSystemMetadataIntentService.wants_indexes(normalized)


def test_columns_search_blocked_during_sql_conversation_but_schema_allowed():
    from app.domain.services.chat_product_route_predicate_service import (
        ChatProductRoutePredicateService,
    )
    from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

    schema_msg = "me mostra o schema da tabela SB1010"
    add_col = "adicione a coluna cidade nessa consulta"

    assert ChatSqlIntentService.is_sql_conversation_turn(add_col)
    assert not ChatSqlIntentService.is_sql_conversation_turn(schema_msg)

    assert ChatProductRoutePredicateService.matches(
        "systemMetadataQuestion",
        schema_msg.lower(),
        message=schema_msg,
    )
    assert ChatProductRoutePredicateService.matches(
        "systemWantsSchema",
        schema_msg.lower(),
        message=schema_msg,
    )
    # columns/search não compete com refinement SQL
    assert not ChatProductRoutePredicateService.matches(
        "systemColumnsSearchAllowed",
        add_col.lower(),
        message=add_col,
    )

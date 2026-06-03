from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)


def test_detects_api_delpi_sql_action():
    action = {
        "actionId": "api_delpi.data.execute_readonly_sql",
        "method": "POST",
        "path": "/data/sql",
        "operationId": "execute_readonly_sql",
        "sensitivity": "sql",
    }

    assert ExternalActionSqlCapabilityService.is_sql_execution_action(action)
    assert ExternalActionSqlCapabilityService.score_sql_execution_action(action) >= 200


def test_detects_internal_provider_sql_action_without_data_sql_path():
    action = {
        "actionId": "internal_analytics.run_readonly_query",
        "method": "POST",
        "path": "/analytics/sql",
        "operationId": "run_sql",
        "sensitivity": "read",
    }

    assert ExternalActionSqlCapabilityService.is_sql_execution_action(action)


def test_detects_sql_action_by_operation_id_only():
    assert ExternalActionSqlCapabilityService.is_sql_execution_context(
        path="/custom/endpoint",
        operation_id="execute_readonly_sql",
        action_id="provider.custom.execute_readonly_sql",
    )


def test_pick_best_sql_action_among_allowed():
    actions = [
        {
            "actionId": "provider.products.search_products",
            "method": "GET",
            "path": "/products/search",
            "operationId": "search_products",
        },
        {
            "actionId": "provider.data.execute_readonly_sql",
            "method": "POST",
            "path": "/data/sql",
            "operationId": "execute_readonly_sql",
            "sensitivity": "sql",
        },
        {
            "actionId": "provider.data.legacy_sql",
            "method": "POST",
            "path": "/legacy/query",
            "operationId": "run_sql",
        },
    ]

    selected = ExternalActionSqlCapabilityService.pick_sql_execution_action(
        actions,
        allowed_action_ids=[
            "provider.products.search_products",
            "provider.data.execute_readonly_sql",
            "provider.data.legacy_sql",
        ],
    )

    assert selected is not None
    assert selected["actionId"] == "provider.data.execute_readonly_sql"


def test_allowed_action_ids_include_sql_for_generic_provider():
    assert ExternalActionSqlCapabilityService.allowed_action_ids_include_sql(
        ["internal_bi.query.run_sql"]
    )


def test_normalize_extracted_sql_preserves_protheus_empty_string_literal():
    sql = (
        "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"
    )

    normalized = ExternalActionSqlCapabilityService.normalize_extracted_sql(sql)

    assert normalized == sql


def test_normalize_extracted_sql_unwraps_double_quoted_statement():
    wrapped = '"select a1_cod from sa1010 where d_e_l_e_t_ = \'\'"'

    normalized = ExternalActionSqlCapabilityService.normalize_extracted_sql(wrapped)

    assert normalized == "select a1_cod from sa1010 where d_e_l_e_t_ = ''"


def test_build_sql_request_body_keeps_trailing_empty_literal():
    body = ExternalActionSqlCapabilityService.build_sql_request_body(
        "select a1_cod from sa1010 where d_e_l_e_t_ = ''"
    )

    assert body["sql"].endswith("= ''")


def test_attach_request_sql_to_nested_payload():
    data = {
        "success": True,
        "data": {
            "success": True,
            "resultsets": [],
        },
    }

    enriched = ExternalActionSqlCapabilityService.attach_request_sql_to_data(
        data,
        arguments={"body": {"query": "SELECT 1"}},
    )

    assert enriched["data"]["sql"] == "SELECT 1"

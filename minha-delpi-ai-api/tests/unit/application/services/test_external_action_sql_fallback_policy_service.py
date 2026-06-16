from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_sql_fallback_policy_service import (
    ExternalActionSqlFallbackPolicyService,
    SqlFallbackRunState,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_fallback_policies_loaded_from_registry() -> None:
    policies = OperationalRouteRegistryService.fallback_policies()

    assert len(policies) >= 5
    assert policies[0]["id"] == "productionSqlPreflight"
    assert OperationalRouteRegistryService.sql_refinement_policy()["reasonKey"] == "sqlRefinement"


def test_inventory_sql_policy_executes_resolver() -> None:
    policy = next(
        policy
        for policy in OperationalRouteRegistryService.fallback_policies()
        if policy.get("id") == "inventorySql"
    )
    select_sql = MagicMock(
        return_value={
            "name": "execute_external_action",
            "arguments": {"actionId": "sql-action", "body": {"sql": "SELECT 1"}},
        }
    )

    selected = ExternalActionSqlFallbackPolicyService.try_policy(
        policy,
        message="Liste os produtos com estoque abaixo do mínimo",
        sql_source="Liste os produtos com estoque abaixo do mínimo",
        allowed_action_ids=["sql-action"],
        select_sql=select_sql,
    )

    assert selected is not None
    select_sql.assert_called_once()
    assert "inventorySqlFastPath" in select_sql.call_args.kwargs["selection_reason_key"]


def test_generic_auto_sql_policy_aborts_when_requires_sql_knowledge() -> None:
    policy = next(
        policy
        for policy in OperationalRouteRegistryService.fallback_policies()
        if policy.get("id") == "genericAutoSql"
    )
    state = SqlFallbackRunState()
    select_sql = MagicMock(return_value=None)

    selected = ExternalActionSqlFallbackPolicyService.try_policy(
        policy,
        message="Liste os produtos com estoque abaixo do mínimo",
        sql_source="Liste os produtos com estoque abaixo do mínimo",
        allowed_action_ids=["sql-action"],
        select_sql=select_sql,
        state=state,
    )

    assert selected is None
    assert state.abort_remaining is True


def test_route_path_marker_for_stock_segment() -> None:
    marker = OperationalRouteRegistryService.route_path_marker_for_segment("stock")

    assert marker == "/stock"


def test_refinement_intent_by_route_segment_includes_stock_structure_parents() -> None:
    mapping = OperationalRouteRegistryService.refinement_intent_by_route_segment()

    assert mapping["stock"] == "stock"
    assert mapping["structure"] == "structure"
    assert mapping["parents"] == "parents"

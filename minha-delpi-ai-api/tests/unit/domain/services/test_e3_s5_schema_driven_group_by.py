"""E3.S5 — group-by schema-driven (sem pathContains como chave)."""

from __future__ import annotations

from app.domain.services.chat_operational_group_by_refinement_service import (
    ChatOperationalGroupByRefinementService,
)
from app.domain.services.schema_driven_group_by_refinement_service import (
    SchemaDrivenGroupByRefinementService,
)


def _consumption_action(*, path: str = "/production/consumption/top-items") -> dict:
    return {
        "enabled": True,
        "method": "GET",
        "path": path,
        "operationId": "whateverRenamed",
        "parametersSchema": [
            {
                "name": "group_by",
                "in": "query",
                "required": False,
                "schema": {
                    "type": "string",
                    "default": "general",
                    "enum": [
                        "general",
                        "product_group",
                        "unit",
                        "branch_summary",
                        "branch",
                    ],
                },
            },
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer"},
            },
        ],
    }


def _vocab_routes() -> list[dict]:
    return ChatOperationalGroupByRefinementService.routes()


def test_e3_s5_extract_capability_requires_group_by_enum():
    capability = SchemaDrivenGroupByRefinementService.extract_capability(
        _consumption_action()
    )
    assert capability is not None
    assert capability.parameter_name == "group_by"
    assert "product_group" in capability.enum_values

    missing = SchemaDrivenGroupByRefinementService.extract_capability(
        {
            "parametersSchema": [
                {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}}
            ]
        }
    )
    assert missing is None


def test_e3_s5_plan_refetch_and_session_without_path_key():
    refetch = SchemaDrivenGroupByRefinementService.plan(
        "agrupe por grupo de produto",
        action=_consumption_action(path="/totally/renamed/endpoint"),
        action_id="production-consumption-top-items",
        previous_parameters={"limit": 50, "group_by": "general"},
        vocabulary_routes=_vocab_routes(),
        path="/totally/renamed/endpoint",
    )
    assert refetch.ok is True
    assert refetch.execution_path == "refetch"
    assert refetch.dimension == "product_group"
    assert refetch.refetch_group_by == "product_group"

    session = SchemaDrivenGroupByRefinementService.plan(
        "consumo por unidade de medida",
        action=_consumption_action(path="/another/rename"),
        action_id="production-consumption-top-items",
        previous_parameters={"limit": 50, "group_by": "general"},
        rows=[
            {"item_code": "1", "unit": "PC", "real_consumption_qty": 10},
            {"item_code": "2", "unit": "KG", "real_consumption_qty": 3},
        ],
        vocabulary_routes=_vocab_routes(),
        path="/another/rename",
    )
    assert session.ok is True
    assert session.execution_path == "session"
    assert session.dimension == "unit"


def test_e3_s5_metamorphic_path_and_operation_id_rename():
    base = SchemaDrivenGroupByRefinementService.plan(
        "agrupe por filial",
        action=_consumption_action(path="/production/consumption/top-items"),
        action_id="production-consumption-top-items",
        previous_parameters={"group_by": "general"},
        vocabulary_routes=_vocab_routes(),
    )
    renamed = SchemaDrivenGroupByRefinementService.plan(
        "agrupe por filial",
        action=_consumption_action(path="/v2/metrics/consumption"),
        action_id="production-consumption-top-items",
        previous_parameters={"group_by": "general"},
        vocabulary_routes=_vocab_routes(),
        path="/v2/metrics/consumption",
    )
    assert base.ok and renamed.ok
    assert base.dimension == renamed.dimension == "branch_summary"
    assert base.execution_path == renamed.execution_path


def test_e3_s5_action_without_group_by_clarifies():
    plan = SchemaDrivenGroupByRefinementService.plan(
        "agrupe por filial",
        action={
            "path": "/products/search",
            "parametersSchema": [
                {"name": "q", "in": "query", "schema": {"type": "string"}},
            ],
        },
        action_id="acme.products.search",
        previous_parameters={},
    )
    assert plan.ok is False
    assert plan.execution_path == "clarify"
    assert plan.clarification_reason == "action_has_no_group_by_parameter"


def test_e3_s5_dimension_outside_enum_clarifies():
    plan = SchemaDrivenGroupByRefinementService.plan(
        "agrupe por cor impossivel",
        action={
            "parametersSchema": [
                {
                    "name": "group_by",
                    "schema": {"type": "string", "enum": ["general", "unit"]},
                }
            ]
        },
        action_id="production-consumption-top-items",
        previous_parameters={"group_by": "general"},
        vocabulary_routes=_vocab_routes(),
    )
    assert plan.ok is False
    assert plan.clarification_reason in {
        "dimension_not_resolved",
        "dimension_not_executable",
    }


def test_e3_s5_legacy_collect_prefers_action_id_over_path():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "production-consumption-top-items",
                            "parameters": {"group_by": "general", "limit": 50},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/renamed/without/marker",
                            "actionId": "production-consumption-top-items",
                        },
                    }
                ]
            },
        }
    ]
    recent = ChatOperationalGroupByRefinementService.collect_recent_action(history)
    assert recent is not None
    assert recent.action_id == "production-consumption-top-items"
    assert recent.route_id == "productionConsumptionTopItems"

    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupamento por grupo da listagem",
        previous_messages=history,
    )
    assert plan is not None
    assert plan.dimension == "product_group"
    assert plan.execution_path == "refetch"

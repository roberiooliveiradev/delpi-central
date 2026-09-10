"""E3.S8 — persist/reload: continuidade via histórico de toolCalls (sem reinferência)."""

from __future__ import annotations

from app.domain.services.chat_operational_follow_up_routing_service import (
    ChatOperationalFollowUpRoutingService,
)
from app.domain.services.chat_operational_group_by_refinement_service import (
    ChatOperationalGroupByRefinementService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.application.services.schema_driven_pagination_filter_service import (
    SchemaDrivenPaginationFilterService,
)


def _assistant_turn(
    *,
    action_id: str,
    path: str,
    parameters: dict,
) -> dict:
    return {
        "role": "assistant",
        "content": "resultado operacional",
        "metadata": {
            "selectedExternalAction": {
                "actionId": action_id,
                "path": path,
                "parameters": dict(parameters),
            },
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": action_id,
                        "parameters": dict(parameters),
                    },
                    "metadata": {
                        "ok": True,
                        "path": path,
                        "actionId": action_id,
                    },
                }
            ],
        },
    }


def test_e3_s8_reload_pagination_from_history_without_llm():
    history = [
        _assistant_turn(
            action_id="acme.products.stock",
            path="/products/10080001/stock",
            parameters={"code": "10080001", "page": 1, "page_size": 20},
        )
    ]
    # Simula F5: só previous_messages (sem snapshot Postgres de lastAction).
    refinements = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "próxima página",
        previous_messages=history,
    )
    assert refinements
    assert refinements[0].page == 2
    assert refinements[0].action_id == "acme.products.stock"


def test_e3_s8_reload_group_by_via_action_id_after_path_rename():
    history = [
        _assistant_turn(
            action_id="production-consumption-top-items",
            path="/renamed/legacy-path-gone",
            parameters={"group_by": "general", "limit": 50},
        )
    ]
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupamento por grupo da listagem",
        previous_messages=history,
    )
    assert plan is not None
    assert plan.action_id == "production-consumption-top-items"
    assert plan.dimension == "product_group"


def test_e3_s8_follow_up_segment_stable_after_cutover():
    assert (
        ChatOperationalFollowUpRoutingService.segment_from_message("e a expedição?")
        == "shipping-status"
    )


def test_e3_s8_schema_filter_reload_uses_inherited_only():
    action = {
        "enabled": True,
        "method": "GET",
        "path": "/products/{code}/stock",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True, "schema": {"type": "string"}},
            {"name": "page", "in": "query", "schema": {"type": "integer"}},
            {"name": "page_size", "in": "query", "schema": {"type": "integer"}},
        ],
    }
    inherited = {"code": "10080001", "page": 4, "page_size": 20}
    plan = SchemaDrivenPaginationFilterService.plan(
        "página 5",
        action=action,
        inherited_parameters=inherited,
        action_id="acme.products.stock",
    )
    assert plan is not None
    assert plan.bind.parameters["page"] == 5
    assert plan.bind.parameters["code"] == "10080001"


def test_e3_s8_message_segment_terms_not_deleted_yet():
    # Cleanup agressivo fica na Onda H; observer API deve permanecer.
    terms = ChatOperationalFollowUpRoutingService.message_segment_terms()
    assert terms
    assert any(segment == "shipping-status" for segment, _ in terms)

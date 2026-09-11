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


def test_e3_s8_message_segment_terms_deleted_e9_s12a():
    # E9.S12.A — DELETE messageSegmentTerms; API vazia.
    assert ChatOperationalFollowUpRoutingService.message_segment_terms() == ()


def test_e3_s8_overlay_last_action_survives_empty_history_enrich():
    """F5 fraco: overlay lastAction permanece após enrich sem toolCalls."""
    from app.application.services.chat_session_memory_service import (
        ChatSessionMemoryService,
    )
    from app.domain.services.chat_conversation_memory_extractor import (
        ChatConversationMemoryExtractor,
    )
    from uuid import uuid4

    class _Repo:
        def load_active_overlay(self, session_id):
            return {
                "operationalFocus": {},
                "behaviorInstructions": {},
                "lastAction": {
                    "name": "stock_lookup",
                    "path": "/products/10080001/stock",
                    "actionId": "acme.products.stock",
                    "params": {"code": "10080001", "page": 1},
                },
            }

        def deactivate_all(self, session_id):
            return 0

        def sync_from_snapshot(self, *args, **kwargs):
            return None

    service = ChatSessionMemoryService(_Repo())
    seeded = service.apply_to_pre_turn(
        session_id=uuid4(),
        snapshot={"operationalFocus": {}, "behaviorInstructions": {}},
        message="próxima página",
    )
    enriched = ChatConversationMemoryExtractor.enrich_snapshot(
        seeded,
        previous_messages=[],
    )
    assert enriched["lastAction"]["actionId"] == "acme.products.stock"

    refinements = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "próxima página",
        previous_messages=[
            _assistant_turn(
                action_id=enriched["lastAction"]["actionId"],
                path=enriched["lastAction"]["path"],
                parameters=dict(enriched["lastAction"]["params"]),
            )
        ],
    )
    assert refinements
    assert refinements[0].page == 2


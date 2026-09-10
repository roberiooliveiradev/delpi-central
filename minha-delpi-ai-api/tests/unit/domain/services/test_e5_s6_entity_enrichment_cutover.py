"""E5.S6 — entity enrichment cutover: goals semânticos + caps (sem scope→route authority)."""

from __future__ import annotations

from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)
from app.domain.services.chat_grounded_enrich_planning_service import (
    ChatGroundedEnrichPlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


class _FakeSelection:
    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
        route_segment=None,
        previous_messages=None,
    ):
        path = "/products/{code}"
        action_id = "ext.products.summary"
        if intent == ChatProductQueryIntent.STOCK or route_segment == "stock":
            path = "/products/{code}/stock"
            action_id = "ext.products.stock"
        elif intent == ChatProductQueryIntent.STRUCTURE or route_segment == "structure":
            path = "/products/{code}/structure"
            action_id = "ext.products.structure"
        elif intent == ChatProductQueryIntent.SALES or route_segment == "sales":
            path = "/products/{code}/sales"
            action_id = "ext.products.sales"
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action_id,
                "parameters": {"code": product_code},
                "path": path,
            },
            "metadata": {},
        }


def _structure_excerpt():
    return {
        "entity": "product_structure",
        "profileKey": "structure",
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["50231850", "10080109"],
        "keysByComponentType": {
            "PI": ["50231850"],
            "MP": ["10080109"],
        },
    }


def test_e5_s6_cutover_flags():
    goals = ChatEntityCapabilityCatalogService.enrich_goals_for_artifact(
        "product_structure",
        "structure",
    )
    assert goals
    assert ChatEntityCapabilityCatalogService.max_extra_routes_per_turn() == 4


def test_e5_s6_product_structure_enrich_via_goals():
    goals = ChatEntityCapabilityCatalogService.enrich_goals_for_artifact(
        "product_structure",
        "structure",
        product_code="90260149",
    )
    assert {goal.scope_label for goal in goals} >= {"stock", "profile"}
    assert all("routeId" not in goal.as_dict() for goal in goals)

    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={"turnGrounding": {"status": "grounded"}},
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )
    assert plan is not None
    assert plan.reason == "grounded_enrich_insight_goal_driven"
    assert "stock" in plan.planned_scopes
    assert "profile" in plan.planned_scopes
    assert plan.max_calls == 4
    assert len(plan.enrich_goals) >= 2


def test_e5_s6_unknown_entity_uses_default_goals_not_route_map():
    group = ChatEntityCapabilityCatalogService.enrich_artifact_group(
        "acme_unknown_widget",
        "weird_profile",
    )
    assert group == "default"
    goals = ChatEntityCapabilityCatalogService.enrich_goals_for_artifact(
        "acme_unknown_widget",
        "weird_profile",
        product_code="X1",
    )
    assert goals
    assert goals[0].scope_label == "profile"

def test_e5_s6_max_routes_by_mode():
    excerpt = _structure_excerpt()
    fast = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={},
        excerpt=excerpt,
        response_mode="fast",
    )
    thinker = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={},
        excerpt=excerpt,
        response_mode="thinker",
    )
    assert fast is not None and thinker is not None
    assert fast.max_calls == 2
    assert thinker.max_calls == 6
    assert thinker.max_fan_out > fast.max_fan_out


def test_e5_s6_mixed_goals_dedupe_actions():
    from app.domain.services.chat_grounded_capability_planning_service import (
        ChatGroundedCapabilityPlanningService,
    )

    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens? também estoque",
        workspace_context={
            "turnGrounding": {"status": "grounded"},
            "behaviorInstructions": {"preferredEnrichScopes": ["sales"]},
        },
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )
    assert plan is not None
    assert "stock" in plan.planned_scopes
    assert "sales" in plan.planned_scopes

    planned = ChatGroundedCapabilityPlanningService._plan_from_enrich_plan(
        _FakeSelection(),
        message="o que me diz sobre os itens?",
        allowed_action_ids=["ext.products.stock", "ext.products.summary", "ext.products.sales"],
        enrich_plan=plan,
    )
    action_ids = [
        str((item.get("arguments") or {}).get("actionId") or "") for item in planned
    ]
    assert len(action_ids) == len(set(action_ids))
    assert len(planned) <= plan.max_calls
    assert all(item.get("metadata", {}).get("entityEnrichGoalDriven") for item in planned)

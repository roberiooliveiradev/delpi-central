"""E5.S2 — baseline freeze: decisões de composição / enrichment / fan-out."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.application.services.chat_playbook_product_action_readiness_service import (
    ChatPlaybookProductActionReadinessService,
)
from app.domain.services.chat_department_meta_composition_planning_service import (
    ChatDepartmentMetaCompositionPlanningService,
)
from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)
from app.domain.services.chat_grounded_enrich_planning_service import (
    ChatGroundedEnrichPlanningService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_sufficiency_critic_service import (
    ChatOperationalSufficiencyCriticService,
)
from app.domain.services.chat_product_enrichment_composition_planning_service import (
    ChatProductEnrichmentCompositionPlanningService,
)
from app.domain.services.chat_product_multi_scope_planning_service import (
    ChatProductMultiScopePlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class _FakeScopeSelectionService:
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
        path = "/products/{code}/analyser"
        if intent == ChatProductQueryIntent.STRUCTURE or route_segment == "structure":
            path = "/products/{code}/structure"
        elif intent == ChatProductQueryIntent.STOCK or route_segment == "stock":
            path = "/products/{code}/stock"
        elif intent == ChatProductQueryIntent.DESCRIPTION:
            path = "/products/{code}"
        elif route_segment == "guide":
            path = "/products/{code}/guide"
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{path}",
                "parameters": {"code": product_code},
                "path": path,
            },
        }


@dataclass(frozen=True)
class CompositionBaselineCase:
    family: str
    message: str
    expected_tool_count_min: int
    expected_tool_count_max: int
    notes: str


# Frozen 2026-09-10 — authority atual (live paths + dead planners como negativo).
_CORPUS: tuple[CompositionBaselineCase, ...] = (
    CompositionBaselineCase(
        family="product_360_overview",
        message="me fale do produto 10080001",
        expected_tool_count_min=0,
        expected_tool_count_max=0,
        notes="looks_like_product_overview=True; composeRouteIds vivos no JSON; .plan DEAD_RUNTIME",
    ),
    CompositionBaselineCase(
        family="structure_plus_stock",
        message="estrutura e estoque do 10080001",
        expected_tool_count_min=2,
        expected_tool_count_max=2,
        notes="multi-scope LIVE via plan_product_scope_fetches",
    ),
    CompositionBaselineCase(
        family="factory_status",
        message="qual o status do produto 90269002 na fabrica hoje?",
        expected_tool_count_min=1,
        expected_tool_count_max=1,
        notes="playbook single-route; scopes multi vazios (sem fan-out)",
    ),
    CompositionBaselineCase(
        family="department_meta_kpi",
        message="painel de indicadores da engenharia",
        expected_tool_count_min=0,
        expected_tool_count_max=0,
        notes="goals_for_department compose≥3; LIVE via E5.S5 (freeze tool_count=0 histórico)",
    ),
    CompositionBaselineCase(
        family="multi_domain_request",
        message="estoque do 10080001 e meta da engenharia",
        expected_tool_count_min=1,
        expected_tool_count_max=1,
        notes="scopes stock + looks_like department; sem planner unificado",
    ),
    CompositionBaselineCase(
        family="result_already_sufficient",
        message="qual o estoque do 10080001?",
        expected_tool_count_min=1,
        expected_tool_count_max=1,
        notes="sem overview; sufficiency→sufficient; sem follow-up auto",
    ),
)


def _structure_excerpt() -> dict:
    return {
        "entity": "product_structure",
        "profileKey": "structure",
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["50231850", "10080109"],
        "keysByComponentType": {
            "PI": ["50231850"],
            "MP": ["10080109", "10090014"],
        },
    }


def test_e5_s2_baseline_covers_required_families():
    families = {case.family for case in _CORPUS}
    required = {
        "product_360_overview",
        "structure_plus_stock",
        "factory_status",
        "department_meta_kpi",
        "multi_domain_request",
        "result_already_sufficient",
    }
    assert families == required


def test_e5_s2_product_360_overview_gate_and_compose_ids():
    case = next(c for c in _CORPUS if c.family == "product_360_overview")
    assert ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        case.message
    )
    assert ChatProductEnrichmentCompositionPlanningService.compose_route_ids() == [
        "productSummary",
        "productStock",
        "productSales",
    ]
    assert not ChatProductMultiScopePlanningService.extract_requested_scopes(case.message)
    # Runtime não orquestra .plan — tool count esperado no corpus = 0 (dead path).
    assert case.expected_tool_count_min == 0
    assert case.expected_tool_count_max == 0


def test_e5_s2_structure_plus_stock_live_multi_scope():
    case = next(c for c in _CORPUS if c.family == "structure_plus_stock")
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(case.message)
    assert scopes == ("structure", "stock")
    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        _FakeScopeSelectionService(),
        message=case.message,
        product_code="10080001",
        allowed_action_ids=["a1"],
    )
    assert case.expected_tool_count_min <= len(planned) <= case.expected_tool_count_max
    paths = {str(item["arguments"].get("path") or "") for item in planned}
    assert "/products/{code}/structure" in paths
    assert "/products/{code}/stock" in paths


def test_e5_s2_factory_status_single_route_no_multi_scope():
    case = next(c for c in _CORPUS if c.family == "factory_status")
    assert ChatPlaybookProductActionReadinessService.matches_playbook_product_intent(
        case.message
    )
    normalized = ChatMessageNormalizationService.normalize_for_matching(case.message)
    assert ChatProductQueryIntentService._looks_like_factory_status_question(normalized)
    assert ChatProductMultiScopePlanningService.extract_requested_scopes(case.message) == ()
    assert case.expected_tool_count_min == case.expected_tool_count_max == 1


def test_e5_s2_department_meta_kpi_compose_routes():
    case = next(c for c in _CORPUS if c.family == "department_meta_kpi")
    assert ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
        case.message
    )
    assert (
        ChatDepartmentMetaCompositionPlanningService.resolve_department_id(case.message)
        == "engineering"
    )
    assert (
        ChatDepartmentMetaCompositionPlanningService.composition_mode(case.message)
        == "compose"
    )
    goals = ChatDepartmentMetaCompositionPlanningService.goals_for_department(
        "engineering",
        mode="compose",
    )
    assert goals[0].goal_id == "dept_meta_indicators"
    assert len(goals) >= 3
    # Freeze histórico: family ainda documenta tool_count=0 no corpus; cutover LIVE = E5.S5.
    assert case.expected_tool_count_min == 0


def test_e5_s2_multi_domain_hybrid_signals():
    case = next(c for c in _CORPUS if c.family == "multi_domain_request")
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(case.message)
    assert scopes == ("stock",)
    assert ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
        case.message
    )
    assert (
        ChatDepartmentMetaCompositionPlanningService.resolve_department_id(case.message)
        == "engineering"
    )
    # Sem planner unificado: multi-scope planeja só o escopo produto (=1).
    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        _FakeScopeSelectionService(),
        message=case.message,
        product_code="10080001",
        allowed_action_ids=["a1"],
    )
    assert case.expected_tool_count_min <= len(planned) <= case.expected_tool_count_max


def test_e5_s2_result_already_sufficient_no_extra_composition():
    case = next(c for c in _CORPUS if c.family == "result_already_sufficient")
    assert not ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        case.message
    )
    assert ChatProductMultiScopePlanningService.extract_requested_scopes(case.message) == (
        "stock",
    )
    verdict = ChatOperationalSufficiencyCriticService.evaluate(
        tool_calls=[
            {
                "arguments": {"path": "/products/10080001/stock", "actionId": "productStock"},
                "ok": True,
            }
        ],
        enrichment_plan={},
        remaining_slots=2,
        user_message=case.message,
    )
    assert verdict.action == "sufficient"
    assert verdict.follow_up_route_ids == []
    assert case.expected_tool_count_min == case.expected_tool_count_max == 1


def test_e5_s2_grounded_enrich_live_after_structure():
    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={"turnGrounding": {"status": "grounded"}},
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )
    assert plan is not None
    assert plan.planned_scopes == ("stock", "profile")
    assert plan.max_calls == 4
    assert {goal.scope_label for goal in plan.enrich_goals} >= {"stock", "profile"}
    assert ChatEntityCapabilityCatalogService.max_extra_routes_per_turn() == 4


def test_e5_s2_dead_runtime_plan_methods_not_wired_in_app():
    """Product enrichment .plan permanece DEAD; department cutover = E5.S5 (LIVE)."""
    app_root = Path(__file__).resolve().parents[4] / "app"
    forbidden = (
        "ChatProductEnrichmentCompositionPlanningService.plan(",
    )
    hits: list[str] = []
    for path in app_root.rglob("*.py"):
        if path.name in {
            "chat_product_enrichment_composition_planning_service.py",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            if needle in text:
                hits.append(f"{path.relative_to(app_root)}:{needle}")
    assert hits == []

    # E5.S5 wired department goal-driven planning into orchestration.
    orchestration = (
        app_root
        / "application"
        / "services"
        / "chat_external_action_orchestration_service.py"
    ).read_text(encoding="utf-8")
    assert "plan_goal_driven" in orchestration
    assert "_enrich_openapi_plan_with_department_meta" in orchestration


def test_e5_s2_budget_caps_deterministic_policy():
    limits = ChatEntityCapabilityCatalogService.enrich_insight_limits_for_mode("normal")
    assert limits["maxExtraRoutes"] == 4
    assert limits["maxFanOut"] == 8
    fast = ChatEntityCapabilityCatalogService.enrich_insight_limits_for_mode("fast")
    thinker = ChatEntityCapabilityCatalogService.enrich_insight_limits_for_mode("thinker")
    assert thinker["maxExtraRoutes"] > fast["maxExtraRoutes"]

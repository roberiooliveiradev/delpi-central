from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_grounded_enrich_planning_service import (
    ChatGroundedEnrichPlanningService,
)

configure_domain_infrastructure_ports()


def _structure_excerpt():
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


def test_build_plan_after_structure_includes_stock_and_profile():
    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={"turnGrounding": {"status": "grounded"}},
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )

    assert plan is not None
    assert "stock" in plan.planned_scopes
    assert "profile" in plan.planned_scopes
    assert plan.product_codes
    assert plan.max_calls == 4


def test_thinker_mode_allows_more_routes_than_fast():
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

    assert fast is not None
    assert thinker is not None
    assert thinker.max_calls > fast.max_calls
    assert thinker.max_fan_out > fast.max_fan_out


def test_behavior_instructions_add_preferred_scopes():
    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={
            "behaviorInstructions": {"preferredEnrichScopes": ["sales"]},
        },
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )

    assert plan is not None
    assert "sales" in plan.planned_scopes


def test_turn_analysis_action_ids_extend_scopes():
    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={
            "turnAnalysis": {"actionIds": ["get_product_stock"]},
        },
        excerpt=_structure_excerpt(),
        response_mode="normal",
    )

    assert plan is not None
    assert "stock" in plan.planned_scopes


def test_user_context_items_fallback_for_product_codes():
    plan = ChatGroundedEnrichPlanningService.build_plan(
        message="o que me diz sobre os itens?",
        workspace_context={
            "workingMemory": {
                "userContextItems": [
                    {
                        "kind": "context",
                        "label": "Produto 10380044",
                        "value": "10380044",
                    }
                ],
                "lastResultExcerpt": {"topKeys": []},
            }
        },
        excerpt={"entity": "product_structure", "profileKey": "structure", "topKeys": []},
        response_mode="normal",
    )

    assert plan is not None
    assert plan.product_codes == ["10380044"]


def test_should_preserve_rag_when_enrich_has_skills_to_load():
    assert ChatGroundedEnrichPlanningService.should_preserve_rag(
        {
            "turnGrounding": {"stage": "grounded_enrich_insight"},
            "turnAnalysisSkillsToLoad": ["company-knowledge"],
        }
    )

    assert not ChatGroundedEnrichPlanningService.should_preserve_rag(
        {
            "turnGrounding": {"stage": "grounded_enrich_insight"},
            "turnAnalysisSkillsToLoad": [],
        }
    )

from app.domain.services.chat_department_meta_composition_planning_service import (
    ChatDepartmentMetaCompositionPlanningService,
)
from tests.fixtures.chat_intelligence_regression_cases import (
    DEPARTMENT_META_COMPOSITION_CASES,
)


def _catalog() -> dict[str, dict]:
    return {
        "ext.dashboard.indicators": {
            "actionId": "ext.dashboard.indicators",
            "whenToUse": "Use for «metas», «realizado» or «department indicators».",
            "summary": "Department metas e realizado indicators",
            "path": "/dashboard/department-indicators",
            "method": "GET",
        },
        "ext.dashboard.idd": {
            "actionId": "ext.dashboard.idd",
            "whenToUse": "Use for «idd» or «indicadores estrategicos».",
            "summary": "Department IDD score",
            "path": "/dashboard/department-idd",
            "method": "GET",
        },
        "ext.kpi.engineering_lmp": {
            "actionId": "ext.kpi.engineering_lmp",
            "whenToUse": "Use for engineering «lmp» KPI.",
            "summary": "Engineering LMP",
            "path": "/kpi/engineering/lmp",
            "method": "GET",
        },
        "ext.kpi.commercial_rol": {
            "actionId": "ext.kpi.commercial_rol",
            "whenToUse": "Use for commercial «rol» KPI.",
            "summary": "Commercial ROL",
            "path": "/kpi/commercial/rol",
            "method": "GET",
        },
    }


def test_looks_like_department_meta_composition():
    assert ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
        "qual a meta para engenharia desse mês?"
    )
    assert not ChatDepartmentMetaCompositionPlanningService.looks_like_department_meta_composition(
        "estoque do produto 10080047"
    )


def test_resolve_department_id_engineering_typo():
    assert (
        ChatDepartmentMetaCompositionPlanningService.resolve_department_id(
            "qual a meta para egenharia desse mês filial 02?"
        )
        == "engineering"
    )


def test_goals_engineering_compose_are_semantic():
    goals = ChatDepartmentMetaCompositionPlanningService.goals_for_department(
        "engineering",
        mode="compose",
    )
    assert goals[0].goal_id == "dept_meta_indicators"
    assert any(goal.goal_id == "dept_idd" for goal in goals)
    assert any("lmp" in goal.query_hints for goal in goals)


def test_composition_mode_primary_vs_compose():
    assert (
        ChatDepartmentMetaCompositionPlanningService.composition_mode(
            "qual a meta para engenharia desse mês?"
        )
        == "primary"
    )
    assert (
        ChatDepartmentMetaCompositionPlanningService.composition_mode(
            "painel de indicadores da engenharia"
        )
        == "compose"
    )


def test_plan_goal_driven_primary_returns_indicators():
    planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
        message="qual a meta para engenharia desse mês?",
        allowed_action_ids=list(_catalog()),
        actions_by_id=_catalog(),
        max_calls=5,
    )
    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "ext.dashboard.indicators"
    assert planned[0]["arguments"]["parameters"]["department_id"] == "engineering"
    assert planned[0]["metadata"]["departmentMetaGoalDriven"] is True


def test_plan_goal_driven_compose_returns_multiple():
    planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
        message="painel de indicadores da engenharia desse mês",
        allowed_action_ids=list(_catalog()),
        actions_by_id=_catalog(),
        max_calls=5,
    )
    assert len(planned) >= 2
    action_ids = [item["arguments"]["actionId"] for item in planned]
    assert "ext.dashboard.indicators" in action_ids
    assert "ext.dashboard.idd" in action_ids


def test_plan_unknown_department_returns_empty():
    planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
        message="qual a meta para marketing desse mês?",
        allowed_action_ids=list(_catalog()),
        actions_by_id=_catalog(),
        max_calls=5,
    )
    assert planned == []


def test_department_meta_composition_regression_cases_goal_driven():
    catalog = _catalog()
    for case in DEPARTMENT_META_COMPOSITION_CASES:
        department_id = ChatDepartmentMetaCompositionPlanningService.resolve_department_id(
            case["message"]
        )
        assert department_id == case["expected_department_id"]
        assert (
            ChatDepartmentMetaCompositionPlanningService.composition_mode(case["message"])
            == case["expected_mode"]
        )
        planned = ChatDepartmentMetaCompositionPlanningService.plan_goal_driven(
            message=case["message"],
            allowed_action_ids=list(catalog),
            actions_by_id=catalog,
            max_calls=5,
        )
        assert len(planned) >= case["expected_min_planned"]
        assert planned[0]["metadata"]["goalId"] == "dept_meta_indicators"

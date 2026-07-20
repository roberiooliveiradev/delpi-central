from app.domain.services.chat_department_meta_composition_planning_service import (
    ChatDepartmentMetaCompositionPlanningService,
)
from tests.fixtures.chat_intelligence_regression_cases import (
    DEPARTMENT_META_COMPOSITION_CASES,
)


class FakeRegistrySelectionService:
    def select_registry_route_id(
        self,
        route_id,
        message,
        *,
        allowed_action_ids=None,
        previous_messages=None,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{route_id}",
                "parameters": {"department_id": "engineering"},
                "routeId": route_id,
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


def test_route_ids_engineering_compose():
    route_ids = ChatDepartmentMetaCompositionPlanningService.route_ids_for_department(
        "engineering",
        mode="compose",
    )

    assert route_ids[0] == "dashboardDepartmentIndicators"
    assert "dashboardDepartmentIdd" in route_ids
    assert "engineeringTransformaSummary" in route_ids
    assert len(route_ids) >= 2


def test_plan_engineering_returns_multiple_actions():
    planned = ChatDepartmentMetaCompositionPlanningService.plan(
        FakeRegistrySelectionService(),
        message="qual a meta para engenharia desse mês?",
        allowed_action_ids=["a", "b", "c"],
        max_calls=5,
    )

    assert len(planned) >= 2
    action_ids = [item["arguments"]["actionId"] for item in planned]

    assert action_ids[0] == "action-dashboardDepartmentIndicators"
    assert "action-dashboardDepartmentIdd" in action_ids


def test_plan_unknown_department_returns_empty():
    planned = ChatDepartmentMetaCompositionPlanningService.plan(
        FakeRegistrySelectionService(),
        message="qual a meta para marketing desse mês?",
        allowed_action_ids=["a"],
        max_calls=5,
    )

    assert planned == []


def test_route_ids_commercial_compose():
    route_ids = ChatDepartmentMetaCompositionPlanningService.route_ids_for_department(
        "commercial",
        mode="compose",
    )

    assert route_ids[0] == "dashboardDepartmentIndicators"
    assert "dashboardDepartmentIdd" in route_ids
    assert "autoTierCHeadOfficeRolTargetPct" in route_ids


def test_plan_commercial_returns_multiple_actions():
    planned = ChatDepartmentMetaCompositionPlanningService.plan(
        FakeRegistrySelectionService(),
        message="qual a meta para comercial desse mês?",
        allowed_action_ids=["a", "b", "c"],
        max_calls=5,
    )

    assert len(planned) >= 2
    assert planned[0]["arguments"]["actionId"] == "action-dashboardDepartmentIndicators"


def test_department_meta_composition_regression_cases():
    for case in DEPARTMENT_META_COMPOSITION_CASES:
        department_id = ChatDepartmentMetaCompositionPlanningService.resolve_department_id(
            case["message"]
        )
        assert department_id == case["expected_department_id"]

        planned = ChatDepartmentMetaCompositionPlanningService.plan(
            FakeRegistrySelectionService(),
            message=case["message"],
            allowed_action_ids=["a", "b", "c"],
            max_calls=5,
        )

        assert len(planned) >= case["expected_min_planned"]
        assert (
            planned[0]["arguments"]["actionId"]
            == f"action-{case['expected_primary_route_id']}"
        )

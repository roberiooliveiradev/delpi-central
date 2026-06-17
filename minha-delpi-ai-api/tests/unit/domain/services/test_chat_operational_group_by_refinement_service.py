from app.domain.services.chat_operational_group_by_refinement_service import (
    ChatOperationalGroupByRefinementService,
)


def _consumption_history(*, group_by: str = "general") -> list[dict]:
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "production-consumption-top-items",
                            "parameters": {
                                "limit": 50,
                                "group_by": group_by,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/production/consumption/top-items",
                            "actionId": "production-consumption-top-items",
                        },
                    }
                ]
            },
        }
    ]


def _consumption_history_with_rows(*, group_by: str = "general") -> list[dict]:
    history = _consumption_history(group_by=group_by)
    history[0]["metadata"]["toolCalls"][0]["metadata"]["tablePresentation"] = {
        "type": "table",
        "rows": [
            {"item_code": "1", "unit": "PC", "real_consumption_qty": 100.0},
            {"item_code": "2", "unit": "KG", "real_consumption_qty": 20.0},
        ],
    }
    return history


def test_plan_follow_up_resolves_product_group_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupamento por grupo da listagem",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "product_group"
    assert plan.execution_path == "refetch"
    assert plan.refetch_group_by == "product_group"


def test_plan_session_follow_up_resolves_unit_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_session_follow_up(
        "consumo por unidade de medida",
        previous_messages=_consumption_history_with_rows(),
    )

    assert plan is not None
    assert plan.dimension == "unit"
    assert plan.execution_path == "session"


def test_plan_refetch_follow_up_for_product_group():
    plan = ChatOperationalGroupByRefinementService.plan_refetch_follow_up(
        "agrupamento por grupo da listagem",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.execution_path == "refetch"


def test_plan_follow_up_resolves_unit_dimension_without_rows_refetches():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "consumo por unidade de medida",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "unit"
    assert plan.execution_path == "refetch"
    assert plan.refetch_group_by == "unit"


def test_plan_follow_up_resolves_unit_dimension_with_rows():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "consumo por unidade de medida",
        previous_messages=_consumption_history_with_rows(),
    )

    assert plan is not None
    assert plan.dimension == "unit"
    assert plan.execution_path == "session"


def test_plan_follow_up_resolves_branch_summary_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupar por filial",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "branch_summary"
    assert plan.execution_path == "refetch"


def test_plan_follow_up_skips_when_dimension_already_active():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupar por grupo",
        previous_messages=_consumption_history(group_by="product_group"),
    )

    assert plan is None

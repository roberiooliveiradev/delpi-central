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


def test_plan_follow_up_resolves_product_group_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupamento por grupo da listagem",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "product_group"
    assert plan.action_id == "production-consumption-top-items"


def test_plan_follow_up_resolves_unit_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "consumo por unidade de medida",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "unit"


def test_plan_follow_up_resolves_branch_summary_dimension():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupar por filial",
        previous_messages=_consumption_history(),
    )

    assert plan is not None
    assert plan.dimension == "branch_summary"


def test_plan_follow_up_skips_when_dimension_already_active():
    plan = ChatOperationalGroupByRefinementService.plan_follow_up(
        "agrupar por grupo",
        previous_messages=_consumption_history(group_by="product_group"),
    )

    assert plan is None

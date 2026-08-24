from app.domain.services.chat_grounded_capability_planning_service import (
    ChatGroundedCapabilityPlanningService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


class _SelectionStub:
    def __init__(self):
        self.calls: list[dict] = []

    def select_action_for_product(self, message, *, product_code, allowed_action_ids, intent, route_segment=None, previous_messages=None):
        self.calls.append(
            {
                "product_code": product_code,
                "intent": intent,
                "route_segment": route_segment,
            }
        )
        return {
            "actionId": f"action-{intent}-{product_code}",
            "intent": intent,
            "productCode": product_code,
        }


def test_plan_stock_fan_out_from_top_keys():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 2,
                "topKeys": ["10380044", "10380045"],
            }
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="e o estoque desses itens?",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert len(planned) == 2
    assert {item["productCode"] for item in planned} == {"10380044", "10380045"}
    assert all(item["intent"] == "stock" for item in planned)


def test_plan_empty_when_narrate_excerpt():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 6,
                "topKeys": ["10380044"],
            }
        },
    }

    assert ChatTurnGroundingService.should_narrate_excerpt(
        "o que me diz sobre os itens?",
        workspace["workingMemory"]["lastResultExcerpt"],
    )

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="o que me diz sobre os itens?",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert planned == []
    assert selection.calls == []

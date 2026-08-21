from app.domain.services.chat_anomaly_follow_up_planning_service import (
    ChatAnomalyFollowUpPlanningService,
)


class FakeSelectionService:
    def select_action_for_product(self, *args, **kwargs):
        intent = kwargs.get("intent")
        segment = kwargs.get("route_segment") or intent
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{segment}",
                "parameters": {"code": "90260148"},
            },
        }

    def select_registry_route_id(self, route_id, message, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{route_id}",
                "parameters": {"code": "90260148"},
            },
        }


def test_stock_low_anomaly_plans_sales_follow_up():
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "action-stock"},
            "metadata": {
                "ok": True,
                "path": "/products/90260148/stock",
                "dataCommentary": {
                    "profileKey": "stock",
                    "anomalies": [{"type": "negative_value"}],
                },
            },
        }
    ]

    planned = ChatAnomalyFollowUpPlanningService.plan_from_tool_calls(
        FakeSelectionService(),
        message="estoque do 90260148",
        tool_calls=tool_calls,
        allowed_action_ids=["a", "b"],
        remaining_slots=2,
    )

    assert len(planned) >= 1
    assert planned[0].get("anomalyFollowUp", {}).get("routeId") == "productSales"


def test_no_follow_up_when_cap_exhausted():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260148/stock",
                "dataCommentary": {
                    "profileKey": "stock",
                    "anomalies": [{"type": "zero_value"}],
                },
            },
        }
    ]

    planned = ChatAnomalyFollowUpPlanningService.plan_from_tool_calls(
        FakeSelectionService(),
        message="estoque do 90260148",
        tool_calls=tool_calls,
        allowed_action_ids=["a"],
        remaining_slots=0,
    )

    assert planned == []


def test_sales_empty_builds_invoice_direction_chips():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260148/sales",
                "emptyResult": True,
                "dataCommentary": {
                    "profileKey": "generic_list",
                    "emptyResult": True,
                    "anomalies": [{"type": "empty_list"}],
                },
            },
        }
    ]

    chips = ChatAnomalyFollowUpPlanningService.build_clarification_suggestions(
        tool_calls,
        message="vendas do 90260148",
    )

    assert len(chips) == 2
    labels = " ".join(item["label"].casefold() for item in chips)
    assert "entrada" in labels
    assert "saída" in labels or "saida" in labels
    assert "90260148" in chips[0]["query"]

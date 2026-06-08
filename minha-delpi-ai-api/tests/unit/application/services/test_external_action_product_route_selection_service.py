from app.application.services.external_actions.external_action_product_route_selection_service import (
    ExternalActionProductRouteSelectionService,
)
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        matches = list(self._actions)[:limit]

        if allowed:
            matches = [
                action
                for action in matches
                if str(action.get("actionId")) in allowed
            ]

        return matches


def test_select_product_prefers_stock_route_for_stock_intent():
    repository = _FakeRepository(
        [
            {
                "actionId": "stock-action",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "analyser-action",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    service = ExternalActionProductRouteSelectionService(repository)

    selected = service.select(
        "estoque do produto 10080055",
        "10080055",
        allowed_action_ids=["stock-action", "analyser-action"],
        intent=ChatProductQueryIntent.STOCK,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080055"

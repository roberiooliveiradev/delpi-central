from app.application.services.external_actions.external_action_kpi_route_selection_service import (
    ExternalActionKpiRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)


def test_kpi_route_selects_supplies_stock_value():
    repository = _FakeRepository(
        [
            {
                "actionId": "supplies-stock-value",
                "method": "GET",
                "path": "/supplies/stock-value",
                "operationId": "get_supplies_stock_value",
                "parametersSchema": [{"name": "top_limit"}],
            }
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)
    kpi_route = ExternalActionKpiRouteSelectionService(route_selection)

    selected = kpi_route.try_select_without_product_code(
        "qual o valor total de estoque da empresa?",
        "qual o valor total de estoque da empresa?",
        allowed_action_ids=["supplies-stock-value"],
        candidates_loader=lambda *args, **kwargs: repository.list_actions(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "supplies-stock-value"


def test_looks_like_cpv_question():
    assert ExternalActionKpiRouteSelectionService.looks_like_cpv_question(
        "qual o cpv do mês?"
    )

from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.domain.services.chat_operational_refinement_service import (
    OperationalRefinement,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)


def test_kpi_try_select_without_product_code_delegates_to_dispatch_registry():
    route_selection = ExternalActionRouteSelectionService(_FakeRepository([]))

    assert (
        route_selection.select_kpi_without_product(
            "qual o cpv do mês?",
            "qual o cpv do mes?",
            allowed_action_ids=["cpv"],
        )
        is None
    )


def test_kpi_metric_refinement_supplies():
    repository = _FakeRepository(
        [
            {
                "actionId": "supplies-otd",
                "method": "GET",
                "path": "/supplies/otd",
                "operationId": "get_supplies_otd",
                "parametersSchema": [],
            }
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)
    refinement = OperationalRefinement(
        kind="metric_refinement",
        metric_kind="supplies",
        metric_path_token="otd",
        reason="Refinamento OTD suprimentos",
    )

    selected = route_selection.select_metric_refinement(
        "otd filial 01",
        refinement,
        allowed_action_ids=["supplies-otd"],
        candidates_loader=lambda *args, **kwargs: repository.list_actions(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "supplies-otd"

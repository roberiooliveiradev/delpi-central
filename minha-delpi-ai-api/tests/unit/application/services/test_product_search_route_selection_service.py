from app.application.services.external_actions.external_action_product_search_route_selection_service import (
    ExternalActionProductSearchRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def find_candidate_actions(self, message, *, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self._actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]


def test_product_search_route_selects_by_group_code():
    repository = _FakeRepository(
        [
            {
                "actionId": "product-search",
                "method": "GET",
                "path": "/products/search",
                "operationId": "search_products",
                "parametersSchema": [
                    {"name": "group_code", "in": "query"},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            }
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)

    selected = route_selection.select_product_search(
        "busque produtos do grupo ABC",
        "busque produtos do grupo abc",
        ["product-search"],
        candidates_loader=lambda *args, **kwargs: repository.find_candidate_actions(
            *args, **kwargs
        ),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "product-search"
    assert selected["arguments"]["parameters"]["group_code"] == "ABC"


def test_looks_like_product_search_ignores_web_request():
    assert not ExternalActionProductSearchRouteSelectionService.looks_like_product_search(
        "pesquise na web sobre delpi conexoes eletricas"
    )

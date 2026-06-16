from app.application.services.external_actions.external_action_product_route_selection_service import (
    ExternalActionProductRouteSelectionService,
)
from app.application.services.external_actions.external_action_vocabulary_route_selection_service import (
    ExternalActionVocabularyRouteSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
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

    def list_actions(self, provider_key=None):
        return list(self._actions)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_select_product_full_without_scope_defers_to_semantic_ranking():
    repository = _FakeRepository(
        [
            {
                "actionId": "analyser-action",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "stock-action",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    service = ExternalActionProductRouteSelectionService(repository)

    selected = service.select(
        "10080055",
        "10080055",
        allowed_action_ids=["stock-action", "analyser-action"],
        intent=ChatProductQueryIntent.FULL,
    )

    assert selected is None


def test_select_vocabulary_fast_path_directives():
    repository = _FakeRepository(
        [
            {
                "actionId": "directives-action",
                "method": "GET",
                "path": "/products/directives/{identifier}",
                "operationId": "get_product_directives",
                "parametersSchema": [
                    {"name": "identifier", "in": "path", "required": True}
                ],
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
    product_route = ExternalActionProductRouteSelectionService(repository)
    service = ExternalActionVocabularyRouteSelectionService(product_route)

    selected = service.select(
        "Diretivas 90260882",
        "diretivas 90260882",
        allowed_action_ids=["directives-action", "analyser-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "directives-action"
    assert selected["arguments"]["parameters"]["identifier"] == "90260882"


def test_select_vocabulary_fast_path_directives_uses_catalog_when_candidates_miss():
    """Regressão: ranking semântico pode omitir /directives/ no top-N."""
    filler = [
        {
            "actionId": f"filler-{index}",
            "method": "GET",
            "path": f"/z-domain/route-{index}",
            "operationId": f"get_z_route_{index}",
            "parametersSchema": [],
        }
        for index in range(80)
    ]
    directives = {
        "actionId": "directives-action",
        "method": "GET",
        "path": "/products/directives/{identifier}",
        "operationId": "get_product_directives",
        "parametersSchema": [{"name": "identifier", "in": "path", "required": True}],
    }
    detail = {
        "actionId": "detail-action",
        "method": "GET",
        "path": "/products/{code}",
        "operationId": "get_product_detail",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
    }
    repository = _FakeRepository([*filler, directives, detail])
    product_route = ExternalActionProductRouteSelectionService(repository)
    service = ExternalActionVocabularyRouteSelectionService(product_route)

    selected = service.select(
        "Diretivas 90260882",
        "diretivas 90260882",
        allowed_action_ids=["directives-action", "detail-action", *[f"filler-{i}" for i in range(80)]],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "directives-action"

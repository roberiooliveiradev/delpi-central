from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_selection_service import (
    ExternalActionProductRouteSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


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


def test_operational_route_selection_picks_exclusive_catalog_without_product_code() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "exclusive-catalog",
                "method": "GET",
                "path": "/products/exclusive-raw-materials/catalog",
                "operationId": "get_exclusive_raw_material_catalog",
                "parametersSchema": [],
            }
        ]
    )
    product_route = ExternalActionProductRouteSelectionService(repository)
    product_route._build_exclusive_catalog_parameters = MagicMock(return_value={"limit": 50})
    service = ExternalActionOperationalRouteSelectionService(product_route)

    selected = service.select(
        "Quais produtos tem mp exclusiva?",
        "quais produtos tem mp exclusiva?",
        allowed_action_ids=["exclusive-catalog"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "exclusive-catalog"


def test_operational_route_selection_picks_factory_status() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "factory-status",
                "method": "GET",
                "path": "/products/{code}/factory-status",
                "operationId": "get_product_factory_status",
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
    product_route = ExternalActionProductRouteSelectionService(repository)
    service = ExternalActionOperationalRouteSelectionService(product_route)

    selected = service.select(
        "Qual o status completo na fábrica do produto 90269002 hoje?",
        "qual o status completo na fabrica do produto 90269002 hoje?",
        allowed_action_ids=["factory-status", "stock-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "factory-status"


def test_operational_route_selection_by_intent_stock() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    product_route = ExternalActionProductRouteSelectionService(repository)
    service = ExternalActionOperationalRouteSelectionService(product_route)

    selected = service.select_by_intent(
        "estoque do produto 10080047",
        "10080047",
        "stock",
        allowed_action_ids=["stock", "analyser"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock"
    assert selected["arguments"]["parameters"]["code"] == "10080047"

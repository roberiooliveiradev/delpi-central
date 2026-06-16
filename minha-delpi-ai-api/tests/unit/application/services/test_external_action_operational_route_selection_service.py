from unittest.mock import MagicMock

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
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
    catalog = ExternalActionProductRouteCatalogService(repository)
    catalog.build_exclusive_catalog_parameters = MagicMock(return_value={"limit": 50})
    service = ExternalActionOperationalRouteSelectionService(catalog)

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
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

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
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_by_intent(
        "estoque do produto 10080047",
        "10080047",
        "stock",
        allowed_action_ids=["stock", "analyser"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock"
    assert selected["arguments"]["parameters"]["code"] == "10080047"


def test_operational_route_selection_production_losses_top() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "production-losses-top-materials",
                "method": "GET",
                "path": "/production/losses/top-materials",
                "operationId": "get_production_losses_top_materials",
                "parametersSchema": [
                    {"name": "date_start"},
                    {"name": "date_end"},
                    {"name": "limit"},
                ],
            }
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_production_operational(
        "Refugos de matéria-prima março filial 02 top 10",
        allowed_action_ids=["production-losses-top-materials"],
        build_date_branch_parameters=lambda action, message, **kwargs: {
            "date_start": "2026-03-01",
            "date_end": "2026-03-31",
            "limit": 10,
        },
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "production-losses-top-materials"


def test_operational_route_selection_sale_orders() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "sale-orders",
                "method": "GET",
                "path": "/commercial/sales",
                "operationId": "list_sale_orders",
                "parametersSchema": [{"name": "page"}, {"name": "page_size"}],
            }
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_sale_orders(
        "Listar ordens de venda de março",
        allowed_action_ids=["sale-orders"],
        merge_date_parameters=lambda action, message, params: {
            **params,
            "date_start": "2026-03-01",
        },
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sale-orders"


def test_operational_route_selection_system_tables_search() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "tables-search",
                "method": "GET",
                "path": "/system/tables/search",
                "operationId": "search_tables",
                "parametersSchema": [{"name": "description", "in": "query"}],
            }
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_system_metadata(
        "qual a tabela de produtos?",
        allowed_action_ids=["tables-search"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "tables-search"
    assert selected["arguments"]["parameters"]["description"] == "produtos"

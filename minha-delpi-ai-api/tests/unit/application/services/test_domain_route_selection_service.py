from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_operational_route_selects_system_table_search():
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
    route_selection = ExternalActionRouteSelectionService(repository)

    selected = route_selection.select_system_metadata(
        "qual a tabela de produtos?",
        ["tables-search"],
        candidates_loader=lambda *args, **kwargs: repository.list_actions(),
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "tables-search"
    assert selected["arguments"]["parameters"]["description"] == "produtos"


def test_operational_route_selects_transforma_processes():
    repository = _FakeRepository(
        [
            {
                "actionId": "transforma-processes",
                "method": "GET",
                "path": "/transforma-mais/processes",
                "operationId": "list_transforma_processes",
                "parametersSchema": [{"name": "branch", "in": "query"}],
            },
            {
                "actionId": "transforma-summary",
                "method": "GET",
                "path": "/transforma-mais/summary",
                "operationId": "get_transforma_summary",
                "parametersSchema": [],
            },
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)

    selected = route_selection.select_transforma(
        "processos do transforma",
        ["transforma-processes", "transforma-summary"],
        candidates_loader=lambda *args, **kwargs: repository.list_actions(),
        build_date_branch_parameters=lambda action, message, **kwargs: {"branch": "01"},
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "transforma-processes"


def test_looks_like_sale_orders_excludes_lmp():
    assert OperationalRouteMatcherService.looks_like_sale_orders_list_question(
        "listar ov da lmp 123"
    ) is False

    assert OperationalRouteMatcherService.looks_like_sale_orders_list_question(
        "listar ordens de venda do periodo"
    ) is True


def test_operational_route_by_intent_respects_allowed_action_ids_order():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.products.get_product_stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "api_externa.products.get_product_stock",
                "method": "GET",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)

    selected = route_selection.select_intent_bound_route(
        "estoque do produto 10080055",
        "10080055",
        intent="stock",
        allowed_action_ids=[
            "api_externa.products.get_product_stock",
            "api_delpi.products.get_product_stock",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_externa.products.get_product_stock"

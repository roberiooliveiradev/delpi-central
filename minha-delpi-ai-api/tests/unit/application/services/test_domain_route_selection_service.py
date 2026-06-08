from app.application.services.external_actions.external_action_domain_route_selection_service import (
    ExternalActionDomainRouteSelectionService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)


def test_domain_route_selects_system_table_search():
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


def test_domain_route_selects_transforma_processes():
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
    assert ExternalActionDomainRouteSelectionService.looks_like_sale_orders_list_question(
        "listar ov da lmp 123"
    ) is False

    assert ExternalActionDomainRouteSelectionService.looks_like_sale_orders_list_question(
        "listar ordens de venda do periodo"
    ) is True

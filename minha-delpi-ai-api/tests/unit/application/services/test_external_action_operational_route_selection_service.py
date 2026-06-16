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


def test_operational_route_selection_picks_product_guide() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "get_product_guide",
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
        "roteiro do produto 90260142",
        "roteiro do produto 90260142",
        allowed_action_ids=["guide", "stock-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "guide"
    assert selected["arguments"]["parameters"]["code"] == "90260142"


def test_operational_route_selection_picks_open_orders() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "open-orders",
                "method": "GET",
                "path": "/products/{code}/sales/open-orders",
                "operationId": "get_product_sales_open_orders",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "sales-summary",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "get_product_sales_summary",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select(
        "carteira de pedidos em aberto do produto 10080047",
        "carteira de pedidos em aberto do produto 10080047",
        allowed_action_ids=["open-orders", "sales-summary"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "open-orders"


def test_operational_route_selection_picks_supplies_cpv() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "cpv",
                "method": "GET",
                "path": "/supplies/cpv",
                "operationId": "get_supplies_cpv",
                "parametersSchema": [{"name": "branch"}],
            }
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select(
        "qual o CPV da filial 01 no último mês",
        "qual o cpv da filial 01 no ultimo mes",
        allowed_action_ids=["cpv"],
        build_date_branch_parameters=lambda action, message, **kwargs: {"branch": "01"},
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "cpv"


def test_operational_route_selection_department_kpi_ebitda() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "ebitda",
                "method": "GET",
                "path": "/financial/ebitda_pct",
                "operationId": "get_ebitda_pct",
                "parametersSchema": [],
            },
            {
                "actionId": "rol-fin",
                "method": "GET",
                "path": "/financial/rol",
                "operationId": "get_rol",
                "parametersSchema": [],
            },
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_by_department_kpi(
        "qual o ebitda do último trimestre",
        allowed_action_ids=["ebitda", "rol-fin"],
        build_date_branch_parameters=lambda action, message, **kwargs: {},
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "ebitda"


def test_operational_route_selection_department_kpi_closing_rate() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "closing",
                "method": "GET",
                "path": "/commercial/closing-rate",
                "operationId": "get_sales_conversion_rate",
                "parametersSchema": [],
            }
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_by_department_kpi(
        "taxa de conversão de vendas",
        allowed_action_ids=["closing"],
        build_date_branch_parameters=lambda action, message, **kwargs: {},
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "closing"


def test_operational_route_selection_picks_product_inspection() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "inspection",
                "method": "GET",
                "path": "/products/{code}/inspection",
                "operationId": "list_product_inspection",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "get_product_guide",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select(
        "inspeção do produto 90260142",
        "inspecao do produto 90260142",
        allowed_action_ids=["inspection", "guide"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "inspection"


def test_operational_route_selection_picks_product_customers() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "customers",
                "method": "GET",
                "path": "/products/{code}/customers",
                "operationId": "get_product_customers",
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
        "clientes do produto 90260142",
        "clientes do produto 90260142",
        allowed_action_ids=["customers", "stock-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "customers"


def test_operational_route_selection_picks_inbound_invoice() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "inbound-invoice",
                "method": "GET",
                "path": "/products/{code}/inbound-invoice",
                "operationId": "get_product_inbound_invoice_items",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "outbound-invoice",
                "method": "GET",
                "path": "/products/{code}/outbound-invoice",
                "operationId": "get_product_outbound_invoice_items",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select(
        "notas de entrada do produto 90260142",
        "notas de entrada do produto 90260142",
        allowed_action_ids=["inbound-invoice", "outbound-invoice"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "inbound-invoice"


def test_operational_route_selection_by_route_segment_continuation() -> None:
    repository = _FakeRepository(
        [
            {
                "actionId": "guide",
                "method": "GET",
                "path": "/products/{code}/guide",
                "operationId": "get_product_guide",
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

    selected = service.select_by_route_segment(
        "filial 02",
        "90260142",
        "guide",
        allowed_action_ids=["guide", "stock-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "guide"
    assert selected["arguments"]["parameters"]["code"] == "90260142"


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

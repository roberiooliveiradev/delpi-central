from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self._actions = actions

    def list_actions(self):
        return list(self._actions)


def test_select_department_kpi_action_by_path_token():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.commercial_otd",
                "method": "GET",
                "path": "/commercial/sales-order-otd",
                "operationId": "getCommercialSalesOrderOtd",
                "parametersSchema": [
                    {"name": "branch", "in": "query"},
                    {"name": "start_date", "in": "query"},
                    {"name": "end_date", "in": "query"},
                ],
            },
            {
                "actionId": "api_delpi.product_sales",
                "method": "GET",
                "path": "/products/{code}/sales",
                "operationId": "getProductSales",
            },
        ]
    )
    service = ExternalActionRouteSelectionService(repository)
    spec = OperationalApiRouteSpec(
        domain="department_kpi",
        reason="OTD comercial",
        path_tokens=("sales-order-otd",),
        path_prefixes=("/commercial/",),
        operation_tokens=("sales_order_otd",),
        parameter_strategy="date_branch",
    )

    selected = service.select(
        spec,
        message="Qual o OTD comercial da filial 01?",
        allowed_action_ids=[
            "api_delpi.commercial_otd",
            "api_delpi.product_sales",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.commercial_otd"
    assert selected["reason"] == "OTD comercial"


def test_select_supplies_metric_prefers_supplies_otd_when_terms_present():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.supplies_otd",
                "method": "GET",
                "path": "/supplies/otd",
                "operationId": "getSuppliesOtd",
                "parametersSchema": [],
            },
            {
                "actionId": "api_delpi.production_otd",
                "method": "GET",
                "path": "/production/otd",
                "operationId": "getProductionOtd",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionRouteSelectionService(repository)
    spec = OperationalApiRouteSpec.from_supplies_metric(
        path_token="otd",
        operation_token="otd",
        reason="OTD de suprimentos",
    )

    selected = service.select(
        spec,
        message="Qual o OTD de suprimentos?",
        allowed_action_ids=[
            "api_delpi.supplies_otd",
            "api_delpi.production_otd",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.supplies_otd"


def test_select_production_otd_detail_when_list_terms_present():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.production_otd_detail",
                "method": "GET",
                "path": "/production/otd",
                "operationId": "get_production_otd",
                "parametersSchema": [],
            },
            {
                "actionId": "api_delpi.production_otd_pct",
                "method": "GET",
                "path": "/production/on_time_delivery_pct",
                "operationId": "get_on_time_delivery_pct",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionRouteSelectionService(repository)
    spec = OperationalApiRouteSpec(
        domain="department_kpi",
        reason="OTD produção",
        path_tokens=("otd",),
        path_prefixes=("/production/",),
        operation_tokens=("production_otd",),
        parameter_strategy="date_branch",
    )

    selected = service.select(
        spec,
        message="Listar OPs atrasadas na produção",
        allowed_action_ids=[
            "api_delpi.production_otd_detail",
            "api_delpi.production_otd_pct",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.production_otd_detail"


def test_select_production_oee_detail_when_list_terms_present():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.production_oee_detail",
                "method": "GET",
                "path": "/production/oee",
                "operationId": "get_production_oee",
                "parametersSchema": [],
            },
            {
                "actionId": "api_delpi.overall_equipment_effectiveness",
                "method": "GET",
                "path": "/production/overall_equipment_effectiveness_pct",
                "operationId": "get_overall_equipment_effectiveness_pct",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionRouteSelectionService(repository)
    spec = OperationalApiRouteSpec(
        domain="department_kpi",
        reason="OEE produção",
        path_tokens=("oee",),
        path_prefixes=("/production/",),
        operation_tokens=("production_oee",),
        parameter_strategy="date_branch",
    )

    selected = service.select(
        spec,
        message="Listar apontamentos OEE fora da faixa",
        allowed_action_ids=[
            "api_delpi.production_oee_detail",
            "api_delpi.overall_equipment_effectiveness",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.production_oee_detail"


def test_select_production_oee_appointment_when_detail_terms_present():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.production_oee_appointment",
                "method": "GET",
                "path": "/production/oee/appointments/{appointment_id}",
                "operationId": "get_production_oee_appointment_by_id",
                "parametersSchema": [{"name": "appointment_id"}],
            },
            {
                "actionId": "api_delpi.production_oee_detail",
                "method": "GET",
                "path": "/production/oee",
                "operationId": "get_production_oee",
                "parametersSchema": [],
            },
        ]
    )
    service = ExternalActionRouteSelectionService(repository)
    spec = OperationalApiRouteSpec(
        domain="department_kpi",
        reason="Detalhe apontamento OEE",
        path_tokens=("oee",),
        path_prefixes=("/production/",),
        operation_tokens=("production_oee",),
        parameter_strategy="date_branch",
    )

    selected = service.select(
        spec,
        message="Detalhe do apontamento OEE com roteiro e tempos previsto x realizado",
        allowed_action_ids=[
            "api_delpi.production_oee_appointment",
            "api_delpi.production_oee_detail",
        ],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.production_oee_appointment"

"""Casos PO — Playbook 15 seleção de rotas operacionais (sem SQL)."""

from __future__ import annotations

from typing import Any


def _operational_route_case(
    case_id: str,
    message: str,
    *,
    action_id: str,
    path: str,
    operation_id: str,
    summary: str,
    parameters: list[str] | None = None,
    extra_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    schema = [{"name": name} for name in (parameters or ["date_start", "date_end", "limit"])]
    actions = [
        {
            "actionId": action_id,
            "method": "GET",
            "path": path,
            "operationId": operation_id,
            "summary": summary,
            "parametersSchema": schema,
        }
    ]

    if extra_actions:
        actions.extend(extra_actions)

    return {
        "id": case_id,
        "message": message,
        "actions": actions,
        "expected_action_id": action_id,
    }


_PRODUCT_PURCHASES_DECOY = {
    "actionId": "purchases",
    "method": "GET",
    "path": "/products/{code}/purchases",
    "operationId": "get_product_purchases",
    "summary": "Compras do produto",
    "parametersSchema": [{"name": "code"}],
}

_PRODUCT_STOCK_DECOY = {
    "actionId": "stock",
    "method": "GET",
    "path": "/products/{code}/stock",
    "operationId": "get_product_stock",
    "summary": "Estoque do produto",
    "parametersSchema": [{"name": "code"}],
}

_QUALITY_NC_DECOY = {
    "actionId": "quality-nonconformities",
    "method": "GET",
    "path": "/quality/nonconformities",
    "operationId": "list_nonconformities",
    "summary": "Não conformidades",
    "parametersSchema": [{"name": "date_start"}, {"name": "date_end"}],
}


PRODUCTION_OPERATIONAL_SELECTION_CASES: list[dict[str, Any]] = [
    _operational_route_case(
        "PO03",
        "Refugos de matéria-prima março filial 02 top 10",
        action_id="production-losses-top-materials",
        path="/production/losses/top-materials",
        operation_id="get_production_losses_top_materials",
        summary="Matérias-primas com mais perdas no período",
        extra_actions=[_QUALITY_NC_DECOY],
    ),
    _operational_route_case(
        "PO03b",
        "Listar registros de refugo detalhado março filial 01",
        action_id="production-losses-records",
        path="/production/losses/records",
        operation_id="get_production_losses_records",
        summary="Registros de perdas no período",
    ),
    _operational_route_case(
        "PO05",
        "Liste as OPs em aberto de hoje filial 01",
        action_id="production-orders-open",
        path="/production/orders/open",
        operation_id="get_production_orders_open",
        summary="OPs em aberto na data",
        parameters=["reference_date", "branch", "limit"],
    ),
    _operational_route_case(
        "PO06",
        "Quais OPs finalizadas hoje?",
        action_id="production-orders-finished",
        path="/production/orders/finished",
        operation_id="get_production_orders_finished",
        summary="OPs finalizadas na data",
        parameters=["reference_date", "limit"],
    ),
    _operational_route_case(
        "PO07",
        "Resumo de OPs por centro de trabalho hoje",
        action_id="production-work-center-order-summary",
        path="/production/work-centers/order-summary",
        operation_id="get_production_work_center_order_summary",
        summary="Resumo de OPs por centro de trabalho",
        parameters=["reference_date", "limit"],
    ),
    _operational_route_case(
        "PO08",
        "Itens com maior consumo por centro de trabalho mês passado top 10",
        action_id="production-consumption-top-items-by-work-center",
        path="/production/consumption/top-items-by-work-center",
        operation_id="get_production_consumption_top_items_by_work_center",
        summary="Consumo por centro de trabalho",
    ),
    _operational_route_case(
        "PO09",
        "Consumo validado por apontamento no mês top 10",
        action_id="production-consumption-top-items-validated",
        path="/production/consumption/top-items-validated",
        operation_id="get_production_consumption_top_items_validated",
        summary="Consumo validado por apontamento",
    ),
    _operational_route_case(
        "PO10",
        "Liste componentes sem empenho hoje filial 01",
        action_id="production-allocation-gaps",
        path="/production/allocation-gaps",
        operation_id="get_production_allocation_gaps",
        summary="Componentes sem empenho",
        parameters=["reference_date", "branch", "limit"],
    ),
    _operational_route_case(
        "PO11",
        "Quais OPs finalizadas sem consumo hoje?",
        action_id="production-orders-finished-without-consumption",
        path="/production/orders/finished-without-consumption",
        operation_id="get_production_orders_finished_without_consumption",
        summary="OPs finalizadas sem baixa de MP",
        parameters=["reference_date", "limit"],
    ),
    _operational_route_case(
        "PO12",
        "Tempo médio planejado por CT hoje",
        action_id="production-work-center-average-planned-time",
        path="/production/work-centers/average-planned-time",
        operation_id="get_production_work_center_average_planned_time",
        summary="Tempo médio planejado por CT",
        parameters=["reference_date", "limit"],
    ),
    _operational_route_case(
        "PO13",
        "Consumo real do item 01010001",
        action_id="production-consumption-by-item",
        path="/production/consumption/by-item/{code}",
        operation_id="get_production_consumption_by_item",
        summary="Consumo real do item por produto",
        parameters=["code", "date_start", "date_end", "limit"],
        extra_actions=[_PRODUCT_STOCK_DECOY],
    ),
    _operational_route_case(
        "PO14",
        "Compare tempo planejado e tempo real das OPs hoje filial 01",
        action_id="production-planned-vs-real-time",
        path="/production/planned-vs-real-time",
        operation_id="get_production_planned_vs_real_time",
        summary="Planejado × real por OP",
        parameters=["reference_date", "branch", "limit"],
    ),
    _operational_route_case(
        "PO15",
        "liste produtos programados para produzir hoje na filial 01",
        action_id="production-schedule-today",
        path="/production/schedule/today",
        operation_id="get_production_schedule_today",
        summary="Programação de produção do dia",
        parameters=["reference_date", "branch", "limit"],
    ),
    _operational_route_case(
        "PO02b",
        "Produtos mais comprados março 2026",
        action_id="purchases-top-products",
        path="/purchases/top-products",
        operation_id="get_purchases_top_products",
        summary="Produtos mais comprados no período",
        extra_actions=[_PRODUCT_PURCHASES_DECOY],
    ),
]

_PLAYBOOK_PRODUCT_HISTORY = [
    {
        "role": "user",
        "content": "O produto 90269002 já começou a produzir hoje?",
    },
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "production-status",
                        "parameters": {
                            "code": "90269002",
                            "reference_date": "18-06-2026",
                            "date_start": "18-06-2026",
                            "date_end": "18-06-2026",
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/90269002/production-status",
                        "actionId": "production-status",
                    },
                }
            ]
        },
    },
]

_PLAYBOOK_STRUCTURE_HISTORY = [
    {
        "role": "user",
        "content": "estrutura do 90260582",
    },
    {
        "role": "assistant",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "structure",
                        "parameters": {"code": "90260582"},
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/90260582/structure",
                        "actionId": "structure",
                    },
                }
            ]
        },
    },
]

OPERATIONAL_FOLLOW_UP_SELECTION_CASES: list[dict[str, Any]] = [
    {
        "id": "FU01",
        "message": "e a expedição?",
        "previous_messages": _PLAYBOOK_PRODUCT_HISTORY,
        "actions": [
            {
                "actionId": "shipping-status",
                "method": "GET",
                "path": "/products/{code}/shipping-status",
                "operationId": "get_product_shipping_status",
                "summary": "Expedição do PA",
                "parametersSchema": [
                    {"name": "code"},
                    {"name": "reference_date"},
                ],
            },
            {
                "actionId": "production-status",
                "method": "GET",
                "path": "/products/{code}/production-status",
                "operationId": "get_product_production_status",
                "summary": "Status de produção",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "inspection",
                "method": "GET",
                "path": "/products/{code}/inspection",
                "operationId": "get_product_inspection",
                "summary": "Inspeção",
                "parametersSchema": [{"name": "code"}],
            },
        ],
        "expected_action_id": "shipping-status",
        "expected_parameters": {
            "code": "90269002",
            "reference_date": "18-06-2026",
        },
    },
    {
        "id": "FU02",
        "message": "quais matérias-primas exclusivas existem na estrutura desse produto?",
        "previous_messages": _PLAYBOOK_PRODUCT_HISTORY,
        "actions": [
            {
                "actionId": "structure-exclusivity",
                "method": "GET",
                "path": "/products/{code}/structure/exclusivity",
                "operationId": "get_product_structure_exclusivity",
                "summary": "Estrutura com exclusividade",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "exclusive-raw-materials-catalog",
                "method": "GET",
                "path": "/products/exclusive-raw-materials/catalog",
                "operationId": "list_exclusive_raw_materials_catalog",
                "summary": "Catálogo global de MPs exclusivas",
                "parametersSchema": [
                    {"name": "view"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "structure-exclusivity",
        "expected_parameters": {"code": "90269002"},
    },
    {
        "id": "FU03",
        "message": "quais são exclusivas?",
        "previous_messages": _PLAYBOOK_STRUCTURE_HISTORY,
        "actions": [
            {
                "actionId": "structure-exclusivity",
                "method": "GET",
                "path": "/products/{code}/structure/exclusivity",
                "operationId": "get_product_structure_exclusivity",
                "summary": "Estrutura com exclusividade",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "structure",
                "method": "GET",
                "path": "/products/{code}/structure",
                "operationId": "get_product_structure",
                "summary": "Estrutura do produto",
                "parametersSchema": [{"name": "code"}],
            },
            {
                "actionId": "exclusive-raw-materials-catalog",
                "method": "GET",
                "path": "/products/exclusive-raw-materials/catalog",
                "operationId": "list_exclusive_raw_materials_catalog",
                "summary": "Catálogo global de MPs exclusivas",
                "parametersSchema": [
                    {"name": "view"},
                    {"name": "limit"},
                ],
            },
        ],
        "expected_action_id": "structure-exclusivity",
        "expected_parameters": {"code": "90260582"},
    },
]

PRODUCTION_OPERATIONAL_SELECTION_CASES.extend(OPERATIONAL_FOLLOW_UP_SELECTION_CASES)

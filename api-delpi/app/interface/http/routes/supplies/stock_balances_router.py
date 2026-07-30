"""Rotas — saldos de estoque por armazém."""

from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.dto.supplies.stock_balances_request import (
    StockBalancesItemsRequest,
    StockBalancesQueryRequest,
)
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import (
    build_get_supplies_stock_balances_items_use_case,
    build_get_supplies_stock_balances_summary_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/stock-balances",
    tags=["Suprimentos — Saldos de estoque"],
)

_SUMMARY_FIELDS = {
    "product_count": {"label": "Qtd. de produtos", "type": "integer"},
    "total_quantity": {"label": "Quantidade total", "type": "number"},
    "total_stock_value": {"label": "Valor do estoque (R$)", "type": "number"},
    "total_stock_value_vatu1": {
        "label": "Valor Protheus VATU1 (R$)",
        "type": "number",
    },
    "warehouse_count": {"label": "Qtd. de armazéns", "type": "integer"},
}

_ITEM_FIELDS = {
    "product_code": {"label": "Produto", "type": "string"},
    "description": {"label": "Descrição", "type": "string"},
    "branch": {"label": "Filial", "type": "string"},
    "warehouse": {"label": "Armazém", "type": "string"},
    "quantity": {"label": "Quantidade", "type": "number"},
    "unit_cost": {"label": "Custo unitário (CM1)", "type": "number"},
    "stock_value": {"label": "Valor (R$)", "type": "number"},
}

_WAREHOUSE_PATTERN = r"^[0-9A-Za-z]{1,10}$"

_SORT_VALUES = (
    "stock_value_desc",
    "stock_value_asc",
    "quantity_desc",
    "quantity_asc",
    "product_code_asc",
    "product_code_desc",
)


def _resolve_warehouse(
    warehouse: str | None,
    location: str | None,
) -> str | None:
    return (warehouse or location or "").strip() or None


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_stock_balances_summary",
        path="/supplies/stock-balances/summary",
    ),
)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_supplies_stock_balances_summary(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    warehouse: str | None = Query(
        default=None,
        description="Warehouse code (B2_LOCAL). Empty = all warehouses.",
        pattern=_WAREHOUSE_PATTERN,
    ),
    location: str | None = Query(
        default=None,
        description="Legacy alias of warehouse — prefer warehouse.",
        pattern=_WAREHOUSE_PATTERN,
        deprecated=True,
    ),
    only_positive: bool = Query(
        default=True,
        description="When true, only rows with B2_QATU > 0.",
    ),
):
    try:
        request = StockBalancesQueryRequest(
            branch=branch,
            warehouse=_resolve_warehouse(warehouse, location),
            only_positive=only_positive,
        )
        use_case = build_get_supplies_stock_balances_summary_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_stock_balances_summary",
            message="Resumo de saldos por armazém buscado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar saldos por armazém: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar saldos por armazém: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar saldos por armazém.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar saldos por armazém: {exc}")
        return error_response(
            "Erro interno ao buscar saldos por armazém.",
            status_code=500,
        )


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_stock_balances_items",
        path="/supplies/stock-balances/items",
    ),
)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_supplies_stock_balances_items(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    warehouse: str | None = Query(
        default=None,
        description="Warehouse code (B2_LOCAL). Empty = all warehouses.",
        pattern=_WAREHOUSE_PATTERN,
    ),
    location: str | None = Query(
        default=None,
        description="Legacy alias of warehouse — prefer warehouse.",
        pattern=_WAREHOUSE_PATTERN,
        deprecated=True,
    ),
    only_positive: bool = Query(
        default=True,
        description="When true, only rows with B2_QATU > 0.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    sort: str = Query(
        default="stock_value_desc",
        description="Sort key for stock balance items.",
        enum=list(_SORT_VALUES),
        pattern="^(" + "|".join(_SORT_VALUES) + ")$",
    ),
):
    try:
        request = StockBalancesItemsRequest(
            branch=branch,
            warehouse=_resolve_warehouse(warehouse, location),
            only_positive=only_positive,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        use_case = build_get_supplies_stock_balances_items_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_stock_balances_items",
            message="Itens de saldo por armazém buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar itens de saldo: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar itens de saldo: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar itens de saldo.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar itens de saldo: {exc}")
        return error_response(
            "Erro interno ao buscar itens de saldo.",
            status_code=500,
        )

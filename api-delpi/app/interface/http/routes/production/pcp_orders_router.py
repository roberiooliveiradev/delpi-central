"""Rotas — catálogo de ordens de produção (view VW_PCP_ORDENS_PRODUCAO)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from delpi_auth.authorization import require_any_permission

from app.application.dto.production.pcp_orders_request import (
    PcpOrdersFilterRequest,
    PcpOrdersItemsRequest,
    PcpOrdersPeriod,
    PcpOrdersRankingRequest,
)
from app.application.security.api_delpi_permissions import KPI_PRODUCTION_ACCESS
from app.composition.pcp_orders_composer import (
    build_get_production_pcp_orders_items_use_case,
    build_get_production_pcp_orders_ranking_use_case,
    build_get_production_pcp_orders_summary_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.domain.production.pcp_orders_view_scope import (
    DEFAULT_ITEMS_SORT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RANKING_LIMIT,
    ITEMS_SORT_VALUES,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
    METRIC_ORDER_QTY,
    METRIC_VALUES,
    RANK_BY_VALUES,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/pcp-orders",
    tags=["Produção — Ordens de produção"],
)

_CODE_PATTERN = r"^.{0,40}$"
_OP_PATTERN = r"^.{0,30}$"

_SUMMARY_FIELDS = {
    "total_orders": {"label": "Total de OPs", "type": "integer"},
    "open_orders": {"label": "OPs em aberto", "type": "integer"},
    "delayed_orders": {"label": "OPs atrasadas", "type": "integer"},
    "mother_orders": {"label": "OPs mãe", "type": "integer"},
    "planned_qty_sum": {"label": "Qtd. planejada", "type": "number"},
    "produced_qty_sum": {"label": "Qtd. apontada", "type": "number"},
    "pending_qty_sum": {"label": "Saldo", "type": "number"},
    "avg_days_late": {"label": "Média dias atraso", "type": "number"},
    "max_days_late": {"label": "Máx. dias atraso", "type": "integer"},
}

_ITEM_FIELDS = {
    "production_order": {"label": "OP", "type": "string"},
    "product_code": {"label": "Produto", "type": "string"},
    "product_description": {"label": "Descrição", "type": "string"},
    "issue_date": {"label": "Emissão", "type": "string", "format": "date"},
    "planned_start_date": {"label": "Início", "type": "string", "format": "date"},
    "due_date": {"label": "Entrega prevista", "type": "string", "format": "date"},
    "planned_qty": {"label": "Quantidade", "type": "number"},
    "pending_qty": {"label": "Saldo", "type": "number"},
    "finish_date": {"label": "Fim real", "type": "string", "format": "date"},
    "days_late": {"label": "Dias atraso", "type": "integer"},
    "observation": {"label": "Observações", "type": "string"},
    "is_open": {"label": "Em aberto", "type": "boolean"},
    "is_mother": {"label": "OP mãe", "type": "boolean"},
    "is_delayed": {"label": "Atrasada", "type": "boolean"},
}

_RANKING_FIELDS = {
    "rank": {"label": "Posição", "type": "integer"},
    "product_code": {"label": "Produto", "type": "string"},
    "product_description": {"label": "Descrição", "type": "string"},
    "warehouse": {"label": "Armazém", "type": "string"},
    "op_key": {"label": "OP", "type": "string"},
    "total_orders": {"label": "Total de OPs", "type": "integer"},
    "order_qty_sum": {"label": "Qtd. ordem", "type": "number"},
    "reported_qty_sum": {"label": "Qtd. apontada", "type": "number"},
    "balance_sum": {"label": "Saldo", "type": "number"},
    "avg_days_late": {"label": "Média atraso", "type": "number"},
}


class PcpOrdersCommonQuery:
    def __init__(
        self,
        branch: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        actual_end_start: str | None = None,
        actual_end_end: str | None = None,
        op_key: str | None = None,
        product_code: str | None = None,
        warehouse: str | None = None,
        mother_only: bool | None = None,
        open_only: bool | None = None,
        delayed_only: bool | None = None,
    ) -> None:
        self.branch = branch
        self.delivery_start = delivery_start
        self.delivery_end = delivery_end
        self.actual_end_start = actual_end_start
        self.actual_end_end = actual_end_end
        self.op_key = op_key
        self.product_code = product_code
        self.warehouse = warehouse
        self.mother_only = mother_only
        self.open_only = open_only
        self.delayed_only = delayed_only


def pcp_orders_common_query(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    delivery_start: Optional[str] = Query(
        default=None,
        description="Delivery date range start (DT_ENTREGA, YYYY-MM-DD).",
    ),
    delivery_end: Optional[str] = Query(
        default=None,
        description="Delivery date range end (DT_ENTREGA, YYYY-MM-DD).",
    ),
    actual_end_start: Optional[str] = Query(
        default=None,
        description="Actual end date range start (DT_REAL_FIM, YYYY-MM-DD).",
    ),
    actual_end_end: Optional[str] = Query(
        default=None,
        description="Actual end date range end (DT_REAL_FIM, YYYY-MM-DD).",
    ),
    op_key: Optional[str] = Query(
        default=None,
        description="Production order key filter (OP_CHAVE).",
        pattern=_OP_PATTERN,
    ),
    product_code: Optional[str] = Query(
        default=None,
        description="Product code filter.",
        pattern=_CODE_PATTERN,
    ),
    warehouse: Optional[str] = Query(
        default=None,
        description="Warehouse code filter.",
        pattern=_CODE_PATTERN,
    ),
    mother_only: Optional[bool] = Query(
        default=None,
        description="When true, only mother production orders (FL_OP_MAE=1).",
    ),
    open_only: Optional[bool] = Query(
        default=None,
        description="When true, only open production orders (FL_OP_EM_ABERTO=1).",
    ),
    delayed_only: Optional[bool] = Query(
        default=None,
        description="When true, only delayed orders (FL_ATRASADA=Sim).",
    ),
) -> PcpOrdersCommonQuery:
    return PcpOrdersCommonQuery(
        branch=branch,
        delivery_start=delivery_start,
        delivery_end=delivery_end,
        actual_end_start=actual_end_start,
        actual_end_end=actual_end_end,
        op_key=op_key,
        product_code=product_code,
        warehouse=warehouse,
        mother_only=mother_only,
        open_only=open_only,
        delayed_only=delayed_only,
    )


def _filter_request(common: PcpOrdersCommonQuery) -> PcpOrdersFilterRequest:
    period = PcpOrdersPeriod.resolve(
        branch=common.branch,
        delivery_start=common.delivery_start,
        delivery_end=common.delivery_end,
    )
    return PcpOrdersFilterRequest.from_params(
        period=period,
        actual_end_start=common.actual_end_start,
        actual_end_end=common.actual_end_end,
        op_key=common.op_key,
        product_code=common.product_code,
        warehouse=common.warehouse,
        mother_only=common.mother_only,
        open_only=common.open_only,
        delayed_only=common.delayed_only,
    )


def _handle_errors(action: str, exc: Exception):
    if isinstance(exc, ValueError):
        log_error(f"Erro de validação ao {action}: {exc}")
        return error_response(str(exc), status_code=400)
    if isinstance(exc, DatabaseConnectionError):
        log_error(f"Erro de banco ao {action}: {exc}")
        return error_response(
            f"Erro de conexão com o banco ao {action}.",
            status_code=503,
        )
    log_error(f"Erro ao {action}: {exc}")
    return error_response(f"Erro interno ao {action}.", status_code=500)


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_pcp_orders_summary",
        path="/production/pcp-orders/summary",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_pcp_orders_summary(
    common: PcpOrdersCommonQuery = Depends(pcp_orders_common_query),
):
    try:
        request = _filter_request(common)
        result = build_get_production_pcp_orders_summary_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_pcp_orders_summary",
            message="Resumo de OPs buscado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar resumo de OPs", exc)


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_pcp_orders_items",
        path="/production/pcp-orders/items",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_pcp_orders_items(
    common: PcpOrdersCommonQuery = Depends(pcp_orders_common_query),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Page size.",
    ),
    sort: str = Query(
        default=DEFAULT_ITEMS_SORT,
        description=f"Sort: {', '.join(ITEMS_SORT_VALUES)}.",
        pattern="^(" + "|".join(ITEMS_SORT_VALUES) + ")$",
    ),
):
    try:
        period = PcpOrdersPeriod.resolve(
            branch=common.branch,
            delivery_start=common.delivery_start,
            delivery_end=common.delivery_end,
        )
        request = PcpOrdersItemsRequest.from_params(
            period=period,
            actual_end_start=common.actual_end_start,
            actual_end_end=common.actual_end_end,
            op_key=common.op_key,
            product_code=common.product_code,
            warehouse=common.warehouse,
            mother_only=common.mother_only,
            open_only=common.open_only,
            delayed_only=common.delayed_only,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        result = build_get_production_pcp_orders_items_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_pcp_orders_items",
            message="Itens de OPs buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar itens de OPs", exc)


@router.get(
    "/ranking",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_pcp_orders_ranking",
        path="/production/pcp-orders/ranking",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_pcp_orders_ranking(
    common: PcpOrdersCommonQuery = Depends(pcp_orders_common_query),
    rank_by: str = Query(
        ...,
        description=f"Ranking dimension: {', '.join(RANK_BY_VALUES)}.",
        pattern="^(" + "|".join(RANK_BY_VALUES) + ")$",
    ),
    metric: str = Query(
        default=METRIC_ORDER_QTY,
        description=f"Metric: {', '.join(METRIC_VALUES)}.",
        pattern="^(" + "|".join(METRIC_VALUES) + ")$",
    ),
    limit: int = Query(
        default=DEFAULT_RANKING_LIMIT,
        ge=1,
        le=MAX_RANKING_LIMIT,
        description="Top-N limit.",
    ),
):
    try:
        period = PcpOrdersPeriod.resolve(
            branch=common.branch,
            delivery_start=common.delivery_start,
            delivery_end=common.delivery_end,
        )
        request = PcpOrdersRankingRequest.from_params(
            period=period,
            rank_by=rank_by,
            metric=metric,
            limit=limit,
            actual_end_start=common.actual_end_start,
            actual_end_end=common.actual_end_end,
            op_key=common.op_key,
            product_code=common.product_code,
            warehouse=common.warehouse,
            mother_only=common.mother_only,
            open_only=common.open_only,
            delayed_only=common.delayed_only,
        )
        result = build_get_production_pcp_orders_ranking_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_pcp_orders_ranking",
            message="Ranking de OPs buscado com sucesso.",
            fields=_RANKING_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar ranking de OPs", exc)

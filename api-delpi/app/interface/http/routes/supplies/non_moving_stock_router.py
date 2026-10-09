"""Rotas — matérias-primas sem giro (GLPI #1197)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.supplies_bff_service_access import (
    require_any_permission_or_supplies_bff,
)
from app.application.dto.supplies.non_moving_stock_request import (
    NonMovingStockItemsRequest,
    NonMovingStockQueryRequest,
)
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import (
    build_get_non_moving_stock_items_use_case,
    build_get_non_moving_stock_summary_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.query_param_enums import (
    BRANCH_SCOPE_CODES_QUERY_OPTIONAL,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/non-moving-stock",
    tags=["Suprimentos — Estoque sem giro"],
)

_SUMMARY_FIELDS = {
    "eligible_stock_value": {
        "label": "Valor elegível (R$)", "type": "number"
    },
    "evaluable_stock_value": {
        "label": "Valor avaliável (R$)", "type": "number"
    },
    "no_consumption_stock_value": {
        "label": "Valor sem giro (R$)", "type": "number"
    },
    "insufficient_history_stock_value": {
        "label": "Valor sem histórico (R$)", "type": "number"
    },
    "non_moving_percentage": {
        "label": "% sem giro", "type": "number"
    },
    "coverage_percentage": {
        "label": "% cobertura", "type": "number"
    },
    "blocked_stock_value": {
        "label": "Valor bloqueado (R$)", "type": "number"
    },
}

_ITEM_FIELDS = {
    "product_code": {"label": "Produto", "type": "string"},
    "description": {"label": "Descrição", "type": "string"},
    "branch": {"label": "Filial", "type": "string"},
    "warehouse": {"label": "Armazém", "type": "string"},
    "quantity": {"label": "Quantidade", "type": "number"},
    "unit_cost": {"label": "Custo unitário (R$)", "type": "number"},
    "stock_value": {"label": "Valor (R$)", "type": "number"},
    "blocked": {"label": "Bloqueado", "type": "boolean"},
    "turnover_status": {"label": "Status de giro", "type": "string"},
    "last_effective_utilization": {
        "label": "Última utilização", "type": "string"
    },
}

_SORT_VALUES = (
    "stock_value_desc",
    "stock_value_asc",
    "quantity_desc",
    "quantity_asc",
    "product_code_asc",
    "product_code_desc",
    "last_utilization_asc",
    "last_utilization_desc",
)

_WAREHOUSE_VALUES = ("01", "99")

_STATUS_VALUES = (
    "WITH_CONSUMPTION",
    "NO_CONSUMPTION_12M",
    "NO_CONSUMPTION_IN_PERIOD",
    "INSUFFICIENT_HISTORY",
)


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_non_moving_stock_summary",
        path="/supplies/non-moving-stock/summary",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def get_supplies_non_moving_stock_summary(
    branch: list[str] | None = BRANCH_SCOPE_CODES_QUERY_OPTIONAL(),
    warehouse: list[str] | None = Query(
        default=None,
        description=(
            "Warehouse filter (B2_LOCAL). Approved scope: 01, 99. "
            "Empty = both."
        ),
    ),
    start_date: str | None = Query(
        default=None,
        description=(
            "Consumption window start (YYYY-MM-DD). Default: 12 months "
            "ago. Requires end_date."
        ),
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str | None = Query(
        default=None,
        description=(
            "Consumption window end, inclusive (YYYY-MM-DD). "
            "Default: today."
        ),
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    try:
        request = NonMovingStockQueryRequest(
            branches=branch,
            warehouses=warehouse,
            start_date=start_date,
            end_date=end_date,
        )
        use_case = build_get_non_moving_stock_summary_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_non_moving_stock_summary",
            message="Resumo de estoque sem giro buscado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar estoque sem giro: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar estoque sem giro: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar estoque sem giro.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar estoque sem giro: {exc}")
        return error_response(
            "Erro interno ao buscar estoque sem giro.",
            status_code=500,
        )


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_non_moving_stock_items",
        path="/supplies/non-moving-stock/items",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def get_supplies_non_moving_stock_items(
    branch: list[str] | None = BRANCH_SCOPE_CODES_QUERY_OPTIONAL(),
    warehouse: list[str] | None = Query(
        default=None,
        description=(
            "Warehouse filter (B2_LOCAL). Approved scope: 01, 99. "
            "Empty = both."
        ),
    ),
    start_date: str | None = Query(
        default=None,
        description="Consumption window start (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str | None = Query(
        default=None,
        description="Consumption window end, inclusive (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    turnover_status: str | None = Query(
        default=None,
        description="Turnover status filter.",
        enum=list(_STATUS_VALUES),
    ),
    blocked: bool | None = Query(
        default=None,
        description="Filter by B1_MSBLQL blocked flag.",
    ),
    product_codes: list[str] | None = Query(
        default=None,
        description="Product code filter (B2_COD). Repeatable or CSV.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY(
        "page_50_500", description="Rows per page (max 500)."
    ),
    sort: str = Query(
        default="stock_value_desc",
        description="Sort key for non-moving stock items.",
        enum=list(_SORT_VALUES),
    ),
):
    try:
        request = NonMovingStockItemsRequest(
            branches=branch,
            warehouses=warehouse,
            start_date=start_date,
            end_date=end_date,
            turnover_status=turnover_status,
            blocked=blocked,
            product_codes=product_codes,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        use_case = build_get_non_moving_stock_items_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_non_moving_stock_items",
            message="Itens de estoque sem giro buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar itens sem giro: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar itens sem giro: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar itens sem giro.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar itens sem giro: {exc}")
        return error_response(
            "Erro interno ao buscar itens sem giro.",
            status_code=500,
        )

"""Rotas — acuracidade do inventário físico (GLPI #1197)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.supplies_bff_service_access import (
    require_any_permission_or_supplies_bff,
)
from app.application.dto.supplies.inventory_accuracy_request import (
    InventoryAccuracyItemsRequest,
    InventoryAccuracyQueryRequest,
)
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import (
    build_get_inventory_accuracy_items_use_case,
    build_get_inventory_accuracy_summary_use_case,
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
    prefix="/supplies/inventory-accuracy",
    tags=["Suprimentos — Acuracidade de inventário"],
)

_SUMMARY_FIELDS = {
    "valid_count_total": {
        "label": "Contagens válidas", "type": "integer"
    },
    "evaluable_count_total": {
        "label": "Contagens avaliáveis", "type": "integer"
    },
    "accurate_count": {"label": "Contagens corretas", "type": "integer"},
    "divergent_count": {
        "label": "Contagens divergentes", "type": "integer"
    },
    "accuracy_percentage": {
        "label": "% acuracidade", "type": "number"
    },
    "coverage_percentage": {
        "label": "% cobertura", "type": "number"
    },
    "shortage_value_total": {
        "label": "Faltas (R$)", "type": "number"
    },
    "surplus_value_total": {
        "label": "Sobras (R$)", "type": "number"
    },
}

_ITEM_FIELDS = {
    "product_code": {"label": "Produto", "type": "string"},
    "description": {"label": "Descrição", "type": "string"},
    "branch": {"label": "Filial", "type": "string"},
    "warehouse": {"label": "Armazém", "type": "string"},
    "count_date": {"label": "Data da contagem", "type": "string"},
    "counted_quantity": {"label": "Quantidade contada", "type": "number"},
    "theoretical_quantity": {
        "label": "Saldo teórico", "type": "number"
    },
    "outcome": {"label": "Resultado", "type": "string"},
    "inventory_document": {
        "label": "Documento de inventário", "type": "string"
    },
}

_SORT_VALUES = (
    "count_date_desc",
    "count_date_asc",
    "product_code_asc",
    "divergence_value_desc",
)

_OUTCOME_VALUES = ("accurate", "divergent", "excluded")


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_inventory_accuracy_summary",
        path="/supplies/inventory-accuracy/summary",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def get_supplies_inventory_accuracy_summary(
    branch: list[str] | None = BRANCH_SCOPE_CODES_QUERY_OPTIONAL(),
    month: str | None = Query(
        default=None,
        description=(
            "Reference month (YYYY-MM). Default: last closed month "
            "(SB9 closing)."
        ),
        pattern=r"^\d{4}-\d{2}$",
    ),
    start_date: str | None = Query(
        default=None,
        description="Custom period start (YYYY-MM-DD). Requires end_date.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str | None = Query(
        default=None,
        description="Custom period end, inclusive (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    try:
        request = InventoryAccuracyQueryRequest(
            branches=branch,
            month=month,
            start_date=start_date,
            end_date=end_date,
        )
        use_case = build_get_inventory_accuracy_summary_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_inventory_accuracy_summary",
            message="Resumo de acuracidade de inventário buscado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar acuracidade: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar acuracidade: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar acuracidade.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar acuracidade: {exc}")
        return error_response(
            "Erro interno ao buscar acuracidade.",
            status_code=500,
        )


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_inventory_accuracy_items",
        path="/supplies/inventory-accuracy/items",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def get_supplies_inventory_accuracy_items(
    branch: list[str] | None = BRANCH_SCOPE_CODES_QUERY_OPTIONAL(),
    month: str | None = Query(
        default=None,
        description="Reference month (YYYY-MM).",
        pattern=r"^\d{4}-\d{2}$",
    ),
    start_date: str | None = Query(
        default=None,
        description="Custom period start (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str | None = Query(
        default=None,
        description="Custom period end, inclusive (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    outcome: str | None = Query(
        default=None,
        description="Outcome filter.",
        enum=list(_OUTCOME_VALUES),
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY(
        "page_50_500", description="Rows per page (max 500)."
    ),
    sort: str = Query(
        default="count_date_desc",
        description="Sort key for inventory accuracy events.",
        enum=list(_SORT_VALUES),
    ),
):
    try:
        request = InventoryAccuracyItemsRequest(
            branches=branch,
            month=month,
            start_date=start_date,
            end_date=end_date,
            outcome=outcome,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        use_case = build_get_inventory_accuracy_items_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_inventory_accuracy_items",
            message="Eventos de acuracidade buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar eventos: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar eventos: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar eventos.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar eventos: {exc}")
        return error_response(
            "Erro interno ao buscar eventos.",
            status_code=500,
        )

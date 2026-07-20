from __future__ import annotations

from typing import Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED as BRANCH_QUERY,
    SAFETY_STOCK_STATUS_QUERY,
    SORT_DIR_QUERY_ALIAS_SORT_DIRECTION,
)

from app.application.dto.supplies.safety_stock_request import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SafetyStockConsumptionAnalysisItemsRequest,
    SafetyStockConsumptionAnalysisQueryRequest,
    SafetyStockItemDetailsRequest,
    SafetyStockItemsRequest,
    SafetyStockQueryRequest,
    SafetyStockSupplierPriceHistoryRequest,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_safety_stock_query_request(
    *,
    branch: str,
    include_blocked: bool = False,
    product_group: Optional[str] = None,
    unit: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    include_without_safety_stock: bool = True,
) -> SafetyStockQueryRequest:
    return SafetyStockQueryRequest(
        branch=branch,
        include_blocked=include_blocked,
        product_group=product_group,
        unit=unit,
        search=search,
        status=status,
        include_without_safety_stock=include_without_safety_stock,
    )


def build_safety_stock_item_details_request(
    *,
    branch: str,
    product_code: str,
    peer_branch: str | None = None,
) -> SafetyStockItemDetailsRequest:
    return SafetyStockItemDetailsRequest(
        branch=branch,
        product_code=product_code,
        peer_branch=peer_branch,
    )


def build_safety_stock_supplier_price_history_request(
    *,
    branch: str,
    product_code: str,
    supplier_code: str,
    supplier_store: str,
) -> SafetyStockSupplierPriceHistoryRequest:
    return SafetyStockSupplierPriceHistoryRequest(
        branch=branch,
        product_code=product_code,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
    )


def build_safety_stock_items_request(
    *,
    branch: str,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    include_blocked: bool = False,
    product_group: Optional[str] = None,
    unit: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    include_without_safety_stock: bool = True,
    sort_by: str = "product_code",
    sort_direction: str = "asc",
) -> SafetyStockItemsRequest:
    return SafetyStockItemsRequest(
        branch=branch,
        page=page,
        page_size=page_size,
        include_blocked=include_blocked,
        product_group=product_group,
        unit=unit,
        search=search,
        status=status,
        include_without_safety_stock=include_without_safety_stock,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


def build_consumption_analysis_query_request(
    *,
    branch: str,
    include_blocked: bool = False,
    product_group: Optional[str] = None,
    unit: Optional[str] = None,
    search: Optional[str] = None,
    analysis_status: Optional[str] = None,
) -> SafetyStockConsumptionAnalysisQueryRequest:
    return SafetyStockConsumptionAnalysisQueryRequest(
        branch=branch,
        include_blocked=include_blocked,
        product_group=product_group,
        unit=unit,
        search=search,
        analysis_status=analysis_status,
    )


def build_consumption_analysis_items_request(
    *,
    branch: str,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    include_blocked: bool = False,
    product_group: Optional[str] = None,
    unit: Optional[str] = None,
    search: Optional[str] = None,
    analysis_status: Optional[str] = None,
    sort_by: str = "difference_quantity",
    sort_direction: str = "asc",
) -> SafetyStockConsumptionAnalysisItemsRequest:
    return SafetyStockConsumptionAnalysisItemsRequest(
        branch=branch,
        page=page,
        page_size=page_size,
        include_blocked=include_blocked,
        product_group=product_group,
        unit=unit,
        search=search,
        analysis_status=analysis_status,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


def execute_safety_stock_route(
    *,
    use_case_builder: Callable[[], object],
    request: (
        SafetyStockQueryRequest
        | SafetyStockItemsRequest
        | SafetyStockItemDetailsRequest
        | SafetyStockConsumptionAnalysisQueryRequest
        | SafetyStockConsumptionAnalysisItemsRequest
    ),
    operation_id: str,
    success_message: str,
    error_context: str,
):
    try:
        use_case = use_case_builder()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id=operation_id,
            message=success_message,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao {error_context}: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError:
        return error_response(
            "Indisponibilidade temporária do Protheus. Tente novamente em instantes.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao {error_context}: {exc}")
        return error_response(
            f"Erro interno ao {error_context}.",
            status_code=500,
        )


def INCLUDE_BLOCKED_QUERY():
    return Query(
    False,
    alias="includeBlocked",
    description="Incluir produtos bloqueados (B1_MSBLQL).",
)
def PRODUCT_GROUP_QUERY():
    return Query(
    None,
    alias="productGroup",
    description="Filtro por grupo de produto (B1_GRUPO).",
)
def UNIT_QUERY():
    return Query(None, description="Filtro por unidade de medida (B1_UM).")
def SEARCH_QUERY():
    return Query(None, description="Busca por código ou descrição do produto.")
def STATUS_QUERY():
    return SAFETY_STOCK_STATUS_QUERY()
def INCLUDE_WITHOUT_SAFETY_STOCK_QUERY():
    return Query(
    True,
    alias="includeWithoutSafetyStock",
    description="Incluir matérias-primas sem estoque de segurança cadastrado.",
)
def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Listing page number.")
def PAGE_SIZE_QUERY():
    return Query(
    DEFAULT_PAGE_SIZE,
    alias="pageSize",
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Registros por página (máximo {MAX_PAGE_SIZE}).",
)
def SORT_BY_QUERY():
    return Query(
    "product_code",
    alias="sortBy",
    description="Campo de ordenação permitido pela API.",
)
def SORT_DIRECTION_QUERY():
    return SORT_DIR_QUERY_ALIAS_SORT_DIRECTION()
def SUPPLIER_STORE_QUERY():
    return Query(
    ...,
    alias="supplierStore",
    min_length=1,
    max_length=6,
    description="Loja do fornecedor (A2_LOJA / D1_LOJA).",
)
ANALYSIS_STATUS_QUERY = Query(
    None,
    alias="analysisStatus",
    description=(
        "Filtro da análise: below_suggested, above_suggested, "
        "adequate ou inconsistent_data."
    ),
)
ANALYSIS_SORT_BY_QUERY = Query(
    "difference_quantity",
    alias="sortBy",
    description="Campo de ordenação da análise de consumo.",
)

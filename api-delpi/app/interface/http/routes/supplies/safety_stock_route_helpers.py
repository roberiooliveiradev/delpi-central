from __future__ import annotations

from typing import Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL as BRANCH_QUERY,
    SAFETY_STOCK_STATUS_QUERY,
    SORT_DIR_QUERY_ALIAS_SORT_DIRECTION,
)

from app.application.dto.supplies.safety_stock_request import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
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
) -> SafetyStockItemDetailsRequest:
    return SafetyStockItemDetailsRequest(
        branch=branch,
        product_code=product_code,
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


def execute_safety_stock_route(
    *,
    use_case_builder: Callable[[], object],
    request: SafetyStockQueryRequest | SafetyStockItemsRequest | SafetyStockItemDetailsRequest,
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


INCLUDE_BLOCKED_QUERY = Query(
    False,
    alias="includeBlocked",
    description="Incluir produtos bloqueados (B1_MSBLQL).",
)
PRODUCT_GROUP_QUERY = Query(
    None,
    alias="productGroup",
    description="Filtro por grupo de produto (B1_GRUPO).",
)
UNIT_QUERY = Query(None, description="Filtro por unidade de medida (B1_UM).")
SEARCH_QUERY = Query(None, description="Busca por código ou descrição do produto.")
STATUS_QUERY = SAFETY_STOCK_STATUS_QUERY
INCLUDE_WITHOUT_SAFETY_STOCK_QUERY = Query(
    True,
    alias="includeWithoutSafetyStock",
    description="Incluir matérias-primas sem estoque de segurança cadastrado.",
)
PAGE_QUERY = Query(DEFAULT_PAGE, ge=1, description="Página da listagem.")
PAGE_SIZE_QUERY = Query(
    DEFAULT_PAGE_SIZE,
    alias="pageSize",
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Registros por página (máximo {MAX_PAGE_SIZE}).",
)
SORT_BY_QUERY = Query(
    "product_code",
    alias="sortBy",
    description="Campo de ordenação permitido pela API.",
)
SORT_DIRECTION_QUERY = SORT_DIR_QUERY_ALIAS_SORT_DIRECTION
SUPPLIER_STORE_QUERY = Query(
    ...,
    alias="supplierStore",
    min_length=1,
    max_length=6,
    description="Loja do fornecedor (A2_LOJA / D1_LOJA).",
)

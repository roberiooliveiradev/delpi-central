"""R06 stock-kardex movement query (MATR910, doc 122).

Guard: S2S-only — the shared ``stock-inventory.read`` scope on the
technical client ``controllership-finance-api`` plus the delegated human
Bearer (ADR-010). Branch is a data filter, not an access boundary (PO
decision, doc 49 §8). The same engine powers the dedicated R07
``inventory-adjustments`` route and the exports (D-O2/D-O3).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Path, Query

from app.application.dto.financeiro_stock_kardex.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DOCUMENT_KIND_ALL,
    DOCUMENT_KIND_INVENT,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.use_cases.financeiro_stock_kardex.export_stock_kardex_use_case import (
    StockKardexExportTruncatedError,
    StockKardexNotExportableError,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.composition.financeiro_stock_kardex_composer import (
    build_export_stock_kardex_use_case,
    build_stock_kardex_summary_use_case,
    build_stock_kardex_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import (
    PAGE_SIZE_QUERY,
    TOP_LIMIT_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    delegated_user_subject,
    export_binary_response,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro — Stock Kardex"],
)

# Same dataset scope as the stock-inventory family (doc 49 §8).
STOCK_KARDEX_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
STOCK_KARDEX_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _stock_kardex_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=STOCK_KARDEX_S2S_REQUIRED_SCOPES,
        allowed_clients=STOCK_KARDEX_S2S_ALLOWED_CLIENTS,
    )(fn)


def _period_query():
    return Query(
        ...,
        description=(
            "Competence in YYYY-MM. The movement window is the full "
            "month; the opening balance reads the previous month-end "
            "SB9 snapshot (never substituted)."
        ),
    )


def _branch_query():
    return Query(
        "all", description="Branch data filter: all | 01 | 02."
    )


def _warehouse_query():
    return Query(
        None,
        description=(
            "Warehouse filter — one or more local codes "
            "(comma-separated)."
        ),
    )


def _product_code_query():
    return Query(None, description="Product code filter (exact).")


def _product_type_query():
    return Query(None, description="Product type filter (B1_TIPO).")


def _movement_kind_query():
    return Query(
        None,
        description="Printed-column filter: entry | output.",
        pattern="^(entry|output)$",
    )


def _page_query():
    return Query(DEFAULT_PAGE, ge=1, description="Page number (min 1).")


def _page_size_query():
    return PAGE_SIZE_QUERY("page_50_200")


def _sort_query():
    return Query(
        "date",
        description="Server-side sort: date | product.",
        pattern="^(date|product)$",
    )


def _sort_dir_query():
    return Query(
        "asc", description="Sort direction.", pattern="^(asc|desc)$"
    )


def _build_request(
    *,
    period: str,
    branch: Optional[str],
    warehouse: Optional[str],
    product_code: Optional[str] = None,
    product_type: Optional[str] = None,
    document_kind: str = DOCUMENT_KIND_ALL,
    movement_kind: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = "date",
    sort_dir: str = "asc",
) -> StockKardexQueryRequest:
    return StockKardexQueryRequest.from_query(
        period=period,
        branch=branch,
        warehouse=warehouse,
        product_code=product_code,
        product_type=product_type,
        document_kind=document_kind,
        movement_kind=movement_kind,
        page=page,
        page_size=page_size,
        sort=sort,
        sort_dir=sort_dir,
    )


def _execute_kardex_route(
    *, use_case_builder, request, operation_id, success_message, error_context
):
    try:
        use_case = use_case_builder()
        result = use_case.execute(
            request, user_subject=delegated_user_subject()
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id=operation_id,
            message=success_message,
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao {error_context}: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao {error_context}: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao {error_context}: {exc}")
        return error_response(
            f"Erro interno ao {error_context}.", status_code=500
        )


def _execute_export_route(
    *,
    request: StockKardexQueryRequest,
    export_format: str,
    operation_id: str,
    error_context: str,
):
    try:
        result = build_export_stock_kardex_use_case().execute(
            request,
            export_format=export_format,
            user_subject=delegated_user_subject(),
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao {error_context}: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except StockKardexNotExportableError:
        return error_response(
            "Relatório indisponível para exportação no estado atual.",
            status_code=409,
            code="not_exportable",
            recoverable=False,
        )
    except StockKardexExportTruncatedError as exc:
        log_error(f"Export kardex truncada: {exc}")
        return error_response(
            "Exportação incompleta — volume acima do limite suportado.",
            status_code=503,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao {error_context}: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao {error_context}: {exc}")
        return error_response(
            f"Erro interno ao {error_context}.", status_code=500
        )
    return export_binary_response(result)


@router.get(
    "/stock-kardex",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_stock_kardex",
        path="/financeiro/stock-kardex",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_stock_kardex_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
    product_type: Optional[str] = _product_type_query(),
    movement_kind: Optional[str] = _movement_kind_query(),
    page: int = _page_query(),
    page_size: int = _page_size_query(),
    sort: str = _sort_query(),
    sort_dir: str = _sort_dir_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            product_type=product_type,
            movement_kind=movement_kind,
            page=page,
            page_size=page_size,
            sort=sort,
            sort_dir=sort_dir,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock-kardex: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_kardex_route(
        use_case_builder=build_stock_kardex_use_case,
        request=request,
        operation_id="get_financeiro_stock_kardex",
        success_message="Stock kardex loaded successfully.",
        error_context="carregar kardex de estoque",
    )


@router.get(
    "/stock-kardex/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_stock_kardex_summary",
        path="/financeiro/stock-kardex/summary",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_stock_kardex_summary_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
    product_type: Optional[str] = _product_type_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            product_type=product_type,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock-kardex summary: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_kardex_route(
        use_case_builder=build_stock_kardex_summary_use_case,
        request=request,
        operation_id="get_financeiro_stock_kardex_summary",
        success_message="Stock kardex summary loaded successfully.",
        error_context="carregar resumo do kardex",
    )


@router.get(
    "/stock-kardex/products/{product_code}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_stock_kardex_product",
        path="/financeiro/stock-kardex/products/{product_code}",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_stock_kardex_product_route(
    product_code: str = Path(..., description="Product code"),
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    page: int = _page_query(),
    page_size: int = _page_size_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            page=page,
            page_size=page_size,
            sort="date",
            sort_dir="asc",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock-kardex product: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_kardex_route(
        use_case_builder=build_stock_kardex_use_case,
        request=request,
        operation_id="get_financeiro_stock_kardex_product",
        success_message="Product kardex loaded successfully.",
        error_context="carregar kardex do produto",
    )


@router.get(
    "/stock-kardex/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_stock_kardex",
        path="/financeiro/stock-kardex/export",
    ),
)
@_stock_kardex_s2s_guard
def export_financeiro_stock_kardex_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
    product_type: Optional[str] = _product_type_query(),
    export_format: str = Query(
        "csv", alias="format", pattern="^(csv|pdf)$"
    ),
):
    from app.application.use_cases.financeiro_stock_kardex.export_stock_kardex_use_case import (
        EXPORT_PAGE_SIZE,
    )

    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            product_type=product_type,
            page=1,
            page_size=EXPORT_PAGE_SIZE,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock-kardex export: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_export_route(
        request=request,
        export_format=export_format,
        operation_id="export_financeiro_stock_kardex",
        error_context="exportar kardex de estoque",
    )


# --- R07 dedicated route (D-O3): the SAME engine constrained to the
# MATR910 inventory slice (SD3 D3_DOC='INVENT').


@router.get(
    "/inventory-adjustments",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inventory_adjustments",
        path="/financeiro/inventory-adjustments",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_inventory_adjustments_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
    movement_kind: Optional[str] = _movement_kind_query(),
    page: int = _page_query(),
    page_size: int = _page_size_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            document_kind=DOCUMENT_KIND_INVENT,
            movement_kind=movement_kind,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em inventory-adjustments: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_kardex_route(
        use_case_builder=build_stock_kardex_use_case,
        request=request,
        operation_id="get_financeiro_inventory_adjustments",
        success_message="Inventory adjustments loaded successfully.",
        error_context="carregar ajustes de inventário",
    )


@router.get(
    "/inventory-adjustments/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inventory_adjustments_summary",
        path="/financeiro/inventory-adjustments/summary",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_inventory_adjustments_summary_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            document_kind=DOCUMENT_KIND_INVENT,
        )
    except ValueError as exc:
        log_error(
            f"Erro de validação em inventory-adjustments summary: {exc}"
        )
        return error_response(str(exc), status_code=400)
    return _execute_kardex_route(
        use_case_builder=build_stock_kardex_summary_use_case,
        request=request,
        operation_id="get_financeiro_inventory_adjustments_summary",
        success_message="Inventory adjustments summary loaded successfully.",
        error_context="carregar resumo de ajustes de inventário",
    )


@router.get(
    "/inventory-adjustments/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_inventory_adjustments",
        path="/financeiro/inventory-adjustments/export",
    ),
)
@_stock_kardex_s2s_guard
def export_financeiro_inventory_adjustments_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    warehouse: Optional[str] = _warehouse_query(),
    product_code: Optional[str] = _product_code_query(),
    export_format: str = Query(
        "csv", alias="format", pattern="^(csv|pdf)$"
    ),
):
    from app.application.use_cases.financeiro_stock_kardex.export_stock_kardex_use_case import (
        EXPORT_PAGE_SIZE,
    )

    try:
        request = _build_request(
            period=period,
            branch=branch,
            warehouse=warehouse,
            product_code=product_code,
            document_kind=DOCUMENT_KIND_INVENT,
            page=1,
            page_size=EXPORT_PAGE_SIZE,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em inventory-adjustments export: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_export_route(
        request=request,
        export_format=export_format,
        operation_id="export_financeiro_inventory_adjustments",
        error_context="exportar ajustes de inventário",
    )


# --- Dedicated CPV contract (D-O1): the governed live CPV measure.


@router.get(
    "/cpv",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_cpv",
        path="/financeiro/cpv",
    ),
)
@_stock_kardex_s2s_guard
def get_financeiro_cpv_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    top_limit: int = TOP_LIMIT_QUERY("top_limit_10_50"),
):
    from app.application.dto.financeiro_stock_kardex.financeiro_cpv_request import (
        FinanceiroCpvRequest,
    )
    from app.composition.financeiro_stock_kardex_composer import (
        build_financeiro_cpv_use_case,
    )

    try:
        request = FinanceiroCpvRequest.from_query(
            period=period, branch=branch, top_limit=top_limit
        )
    except ValueError as exc:
        log_error(f"Erro de validação em financeiro cpv: {exc}")
        return error_response(str(exc), status_code=400)
    try:
        result = build_financeiro_cpv_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
        return api_delpi_success(
            result,
            operation_id="get_financeiro_cpv",
            message="CPV loaded successfully.",
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao carregar CPV: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar CPV: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar CPV: {exc}")
        return error_response(
            "Erro interno ao carregar o CPV.", status_code=500
        )

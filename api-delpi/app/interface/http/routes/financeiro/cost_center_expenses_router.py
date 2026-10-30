"""R10 cost-center-expenses query (doc 126, IMPLEMENTATION-STAGE-01).

Guard: S2S-only — the shared ``stock-inventory.read`` scope on the
technical client ``controllership-finance-api`` plus the delegated human
Bearer (ADR-010). Branch is a data filter, not an access boundary (PO
decision, doc 49 §8). Two strict universes: ``calculation`` (documented
historical selection) and ``investigation`` (in-competence rows outside
the selection) — totals never combined (doc 127 §3).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.application.dto.financeiro_cost_center_expenses.cost_center_expenses_request import (
    CostCenterExpensesRequest,
)
from app.application.dto.financeiro_cost_center_expenses.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.application.use_cases.financeiro_cost_center_expenses.export_cost_center_expenses_use_case import (
    EXPORT_PAGE_SIZE,
    CostCenterExpensesExportTruncatedError,
    CostCenterExpensesNotExportableError,
)
from app.composition.financeiro_cost_center_expenses_composer import (
    build_cost_center_expenses_use_case,
    build_export_cost_center_expenses_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    delegated_user_subject,
    export_binary_response,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro — Cost Center Expenses"],
)

# Same dataset scope as the stock-inventory family (doc 49 §8).
COST_CENTER_EXPENSES_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
COST_CENTER_EXPENSES_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _cost_center_expenses_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=COST_CENTER_EXPENSES_S2S_REQUIRED_SCOPES,
        allowed_clients=COST_CENTER_EXPENSES_S2S_ALLOWED_CLIENTS,
    )(fn)


def _period_query():
    return Query(
        ...,
        description=(
            "Competence in YYYY-MM. The window is the full month over "
            "the D1_DTDIGIT axis (never D1_EMISSAO)."
        ),
    )


def _branch_query():
    return Query(
        "all", description="Branch data filter: all | 01 | 02."
    )


def _universe_query():
    return Query(
        "calculation",
        description=(
            "Universe: calculation (official selection) | investigation "
            "(in-competence rows outside the selection)."
        ),
        pattern="^(calculation|investigation)$",
    )


def _view_query():
    return Query(
        "all",
        description="Listing view: all | divergences | unclassified.",
        pattern="^(all|divergences|unclassified)$",
    )


def _include_findings_query():
    return Query(
        True,
        description="Materialize findings[] (POSSIBLE_DIVERGENCE).",
    )


def _page_query():
    return Query(DEFAULT_PAGE, ge=1, description="Page number (min 1).")


def _page_size_query():
    return PAGE_SIZE_QUERY("page_50_200")


def _sort_query():
    return Query(
        "date",
        description=(
            "Server-side sort: date | document | cost_center | "
            "product | total_value."
        ),
        pattern="^(date|document|cost_center|product|total_value)$",
    )


def _sort_dir_query():
    return Query(
        "asc", description="Sort direction.", pattern="^(asc|desc)$"
    )


def _build_request(
    *,
    period: str,
    branch: Optional[str],
    universe: str,
    view: str,
    cost_center: Optional[str],
    product_code: Optional[str],
    document: Optional[str],
    supplier_code: Optional[str],
    tes: Optional[str],
    include_findings: bool,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str = "date",
    sort_dir: str = "asc",
) -> CostCenterExpensesRequest:
    return CostCenterExpensesRequest.from_query(
        period=period,
        branch=branch,
        universe=universe,
        view=view,
        cost_center=cost_center,
        product_code=product_code,
        document=document,
        supplier_code=supplier_code,
        tes=tes,
        include_findings=include_findings,
        page=page,
        page_size=page_size,
        sort=sort,
        sort_dir=sort_dir,
    )


def _execute_route(
    *, request: CostCenterExpensesRequest, operation_id: str
):
    try:
        result = build_cost_center_expenses_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id=operation_id,
            message="Cost center expenses loaded successfully.",
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(
            f"Escopo financeiro não resolvido ao carregar R10: {exc}"
        )
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em cost-center-expenses: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar R10: {exc}")
        return error_response(
            "Erro interno ao carregar despesas por centro de custo.",
            status_code=500,
        )


@router.get(
    "/cost-center-expenses",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_cost_center_expenses",
        path="/financeiro/cost-center-expenses",
    ),
)
@_cost_center_expenses_s2s_guard
def get_financeiro_cost_center_expenses_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    universe: str = _universe_query(),
    view: str = _view_query(),
    cost_center: Optional[str] = Query(
        None, description="Cost center filter (exact)."
    ),
    product_code: Optional[str] = Query(
        None, description="Product code filter (exact)."
    ),
    document: Optional[str] = Query(
        None, description="Document number filter (exact)."
    ),
    supplier_code: Optional[str] = Query(
        None, description="Supplier code filter (exact)."
    ),
    tes: Optional[str] = Query(
        None, description="TES filter (exact)."
    ),
    include_findings: bool = _include_findings_query(),
    page: int = _page_query(),
    page_size: int = _page_size_query(),
    sort: str = _sort_query(),
    sort_dir: str = _sort_dir_query(),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            universe=universe,
            view=view,
            cost_center=cost_center,
            product_code=product_code,
            document=document,
            supplier_code=supplier_code,
            tes=tes,
            include_findings=include_findings,
            page=page,
            page_size=page_size,
            sort=sort,
            sort_dir=sort_dir,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em cost-center-expenses: {exc}")
        return error_response(str(exc), status_code=400)
    return _execute_route(
        request=request,
        operation_id="get_financeiro_cost_center_expenses",
    )


@router.get(
    "/cost-center-expenses/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_cost_center_expenses",
        path="/financeiro/cost-center-expenses/export",
    ),
)
@_cost_center_expenses_s2s_guard
def export_financeiro_cost_center_expenses_route(
    period: str = _period_query(),
    branch: Optional[str] = _branch_query(),
    universe: str = _universe_query(),
    view: str = _view_query(),
    cost_center: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    document: Optional[str] = Query(None),
    supplier_code: Optional[str] = Query(None),
    tes: Optional[str] = Query(None),
    export_format: str = Query(
        "csv", alias="format", pattern="^(csv|pdf)$"
    ),
):
    try:
        request = _build_request(
            period=period,
            branch=branch,
            universe=universe,
            view=view,
            cost_center=cost_center,
            product_code=product_code,
            document=document,
            supplier_code=supplier_code,
            tes=tes,
            include_findings=True,
            page=1,
            page_size=EXPORT_PAGE_SIZE,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em cost-center-expenses export: {exc}")
        return error_response(str(exc), status_code=400)
    try:
        result = build_export_cost_center_expenses_use_case().execute(
            request,
            export_format=export_format,
            user_subject=delegated_user_subject(),
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido no export R10: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except CostCenterExpensesNotExportableError:
        return error_response(
            "Relatório indisponível para exportação no estado atual.",
            status_code=409,
            code="not_exportable",
            recoverable=False,
        )
    except CostCenterExpensesExportTruncatedError as exc:
        log_error(f"Export R10 truncada: {exc}")
        return error_response(
            "Exportação incompleta — volume acima do limite suportado.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao exportar R10: {exc}")
        return error_response(
            "Erro interno ao exportar despesas por centro de custo.",
            status_code=500,
        )
    return export_binary_response(result)

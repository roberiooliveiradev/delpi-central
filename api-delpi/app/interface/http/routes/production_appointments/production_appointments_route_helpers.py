from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    PRODUCTION_APPOINTMENTS_GROUP_BY_QUERY,
)

from app.application.dto.production_appointments.production_appointments_query_request import (
    ProductionAppointmentsQueryRequest,
)
from app.core.responses import error_response
from app.domain.production.production_appointments.production_appointments_scope import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_query_request(
    *,
    branch: str,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    work_center: Optional[str] = None,
    op: Optional[str] = None,
    product: Optional[str] = None,
    search: Optional[str] = None,
    group_by: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> ProductionAppointmentsQueryRequest:
    return ProductionAppointmentsQueryRequest.from_query(
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        work_center=work_center,
        op=op,
        product=product,
        search=search,
        group_by=group_by,
        page=page,
        page_size=page_size,
    )


def execute_route(
    *,
    use_case_builder: Callable[[], object],
    request: Any,
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
    except Exception as exc:
        log_error(f"Erro ao {error_context}: {exc}")
        return error_response(
            f"Erro interno ao {error_context}.",
            status_code=500,
        )


def BRANCH_QUERY():
    return BRANCH_QUERY_REQUIRED()
def WORK_CENTER_QUERY():
    return Query(None, description="Work center filter (e.g. CT-70).")
def OP_QUERY():
    return Query(None, description="Production order filter.")
def PRODUCT_QUERY():
    return Query(None, description="Product code filter.")
def SEARCH_QUERY():
    return Query(
        None,
        description=(
            "Optional free-text search across visible table columns "
            "(operator, OP, product, work center, resource, etc.)."
        ),
    )
def GROUP_BY_QUERY():
    return PRODUCTION_APPOINTMENTS_GROUP_BY_QUERY()
def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Listing page number.")
def PAGE_SIZE_QUERY():
    return Query(
    DEFAULT_PAGE_SIZE,
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Registros por página (máximo {MAX_PAGE_SIZE}).",
)

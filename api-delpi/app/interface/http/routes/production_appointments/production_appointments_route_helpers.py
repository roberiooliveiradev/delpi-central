from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

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


BRANCH_QUERY = Query(
    ...,
    min_length=2,
    max_length=2,
    pattern="^(01|02)$",
    description='Filial Protheus ("01" = SC, "02" = ES).',
)
DATE_START_QUERY = Query(
    None,
    description="Data inicial (YYYY-MM-DD). Padrão: 1º dia do mês atual.",
)
DATE_END_QUERY = Query(
    None,
    description="Data final inclusiva (YYYY-MM-DD). Padrão: fim do mês corrente.",
)
WORK_CENTER_QUERY = Query(None, description="Filtro por centro de trabalho (ex.: CT-70).")
OP_QUERY = Query(None, description="Filtro por ordem de produção.")
PRODUCT_QUERY = Query(None, description="Filtro por código de produto.")
GROUP_BY_QUERY = Query(
    "day",
    pattern="^(day|day_work_center)$",
    description='Agregação da série: "day" ou "day_work_center".',
)
PAGE_QUERY = Query(DEFAULT_PAGE, ge=1, description="Página da listagem.")
PAGE_SIZE_QUERY = Query(
    DEFAULT_PAGE_SIZE,
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Registros por página (máximo {MAX_PAGE_SIZE}).",
)

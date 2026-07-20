from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    GRANULARITY_QUERY_DAY_MONTH_AUTO,
    REFUGOS_DIMENSION_QUERY,
)

from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.application.dto.refugos.refugos_registros_request import RefugosRegistrosRequest
from app.application.dto.refugos.refugos_serie_request import RefugosSerieRequest
from app.core.responses import error_response
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RANKING_LIMIT,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_refugos_query_request(
    *,
    filial: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    dimension: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
    limit: Optional[int] = None,
) -> RefugosQueryRequest:
    return RefugosQueryRequest.from_query(
        filial=filial,
        data_inicio=data_inicio,
        data_fim=data_fim,
        dimension=dimension,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
        limit=limit,
    )


def build_refugos_serie_request(
    *,
    filial: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    granularity: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
) -> RefugosSerieRequest:
    return RefugosSerieRequest.from_query(
        filial=filial,
        data_inicio=data_inicio,
        data_fim=data_fim,
        granularity=granularity,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
    )


def build_refugos_registros_request(
    *,
    filial: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> RefugosRegistrosRequest:
    return RefugosRegistrosRequest.from_query(
        filial=filial,
        data_inicio=data_inicio,
        data_fim=data_fim,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
        page=page,
        page_size=page_size,
    )


def execute_refugos_route(
    *,
    use_case_builder: Callable[[], object],
    request: Any | None,
    operation_id: str,
    success_message: str,
    error_context: str,
):
    try:
        use_case = use_case_builder()
        result = use_case.execute(request) if request is not None else use_case.execute()
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


def FILIAL_QUERY():
    return BRANCH_QUERY_REQUIRED()
def DATA_INICIO_QUERY():
    return Query(
    None,
    alias="dataInicio",
    description="Start date (YYYY-MM-DD). Default: first day of current month.", json_schema_extra={"format": "date"},
)
def DATA_FIM_QUERY():
    return Query(
    None,
    alias="dataFim",
    description="End date (YYYY-MM-DD). Default: today.", json_schema_extra={"format": "date"},
)
def DIMENSION_QUERY():
    return REFUGOS_DIMENSION_QUERY()
def MP_QUERY():
    return Query(None, description="Raw material code filter.")
def PA_QUERY():
    return Query(None, description="Finished product code filter.")
def OP_QUERY():
    return Query(None, description="Production order filter.")
def MOTIVO_QUERY():
    return Query(None, description="Reason code filter (CYO).")
def RECURSO_QUERY():
    return Query(
    None,
    alias="centroTrabalho",
    description="Work center filter (BC_RECURSO).",
)
def LIMIT_QUERY():
    return Query(
    DEFAULT_RANKING_LIMIT,
    ge=1,
    le=MAX_RANKING_LIMIT,
    description="Maximum ranking items.",
)
def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Listing page number.")
def PAGE_SIZE_QUERY():
    return Query(
    DEFAULT_PAGE_SIZE,
    alias="pageSize",
    ge=1,
    le=MAX_PAGE_SIZE,
    description="Rows per page (maximum 100).",
)
def GRANULARITY_QUERY():
    return GRANULARITY_QUERY_DAY_MONTH_AUTO()
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
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
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_refugos_query_request(
    *,
    filial: str | None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    dimension: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
    limit: Optional[int] = None,
    require_filial: bool = True,
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
        require_filial=require_filial,
    )


def build_refugos_serie_request(
    *,
    filial: str | None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    granularity: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
    require_filial: bool = True,
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
        require_filial=require_filial,
    )


def build_refugos_registros_request(
    *,
    filial: str | None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    mp: Optional[str] = None,
    pa: Optional[str] = None,
    op: Optional[str] = None,
    motivo: Optional[str] = None,
    recurso: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    require_filial: bool = True,
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
        require_filial=require_filial,
    )


def execute_refugos_route(
    *,
    use_case_builder: Callable[[], object],
    request: Any | None,
    operation_id: str,
    success_message: str,
    error_context: str,
    fields: dict[str, str] | None = None,
    field_formats: dict[str, str] | None = None,
):
    try:
        use_case = use_case_builder()
        result = use_case.execute(request) if request is not None else use_case.execute()
        return api_delpi_success(
            result,
            operation_id=operation_id,
            message=success_message,
            fields=fields,
            field_formats=field_formats,
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


def FILIAL_QUERY_OPTIONAL():
    return BRANCH_QUERY_OPTIONAL()


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
    """Delegate to canonical pagination tier `limit_ranking_10_50`."""
    from app.interface.http.pagination_query import LIMIT_QUERY as _canonical
    return _canonical("limit_ranking_10_50")

def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Listing page number.")
def PAGE_SIZE_QUERY():
    """Delegate to canonical pagination tier `page_50_100`."""
    from app.interface.http.pagination_query import PAGE_SIZE_QUERY as _canonical
    return _canonical("page_50_100")

def GRANULARITY_QUERY():
    return GRANULARITY_QUERY_DAY_MONTH_AUTO()
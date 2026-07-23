from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    BRANCH_QUERY_REQUIRED,
    RETRABALHO_ORDER_BY_DETALHES_QUERY,
    RETRABALHO_ORDER_BY_RANKING_QUERY,
    SORT_DIR_QUERY_ALIAS_ORDER_DIR_DESC,
)

from app.application.dto.retrabalho.retrabalho_detalhes_request import RetrabalhoDetalhesRequest
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_query_settings import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RANKING_LIMIT,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
)
from app.utils.logger import log_error


def build_retrabalho_query_request(
    *,
    filial: str | None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    recurso: Optional[str] = None,
    centro_custo: Optional[str] = None,
    codigo_operador: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    require_filial: bool = True,
) -> RetrabalhoQueryRequest:
    return RetrabalhoQueryRequest.from_query(
        filial=filial,
        data_inicio=data_inicio,
        data_fim=data_fim,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
        order_by=order_by,
        limit=limit,
        require_filial=require_filial,
    )


def build_retrabalho_detalhes_request(
    *,
    filial: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    recurso: Optional[str] = None,
    centro_custo: Optional[str] = None,
    codigo_operador: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    order_by: Optional[str] = None,
    order_dir: Optional[str] = None,
) -> RetrabalhoDetalhesRequest:
    return RetrabalhoDetalhesRequest.from_query(
        filial=filial,
        data_inicio=data_inicio,
        data_fim=data_fim,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


def execute_retrabalho_route(
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

        payload = result.to_dict() if hasattr(result, "to_dict") else result

        return api_delpi_success(
            payload,
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


def FILIAL_QUERY_OPTIONAL():
    return BRANCH_QUERY_OPTIONAL()


def DATA_INICIO_QUERY():
    return Query(
    None,
    alias="dataInicio",
    description="Start date (YYYY-MM-DD). Default: last 12 months.", json_schema_extra={"format": "date"},
)
def DATA_FIM_QUERY():
    return Query(
    None,
    alias="dataFim",
    description="End date (YYYY-MM-DD). Default: today.", json_schema_extra={"format": "date"},
)
def RECURSO_QUERY():
    return Query(None, description="Resource filter.")
def CENTRO_CUSTO_QUERY():
    return Query(None, alias="centroCusto", description="Cost center filter.")
def CODIGO_OPERADOR_QUERY():
    return Query(
    None,
    alias="codigoOperador",
    description="Operator code filter.",
)
def ORDER_BY_RANKING_QUERY():
    return RETRABALHO_ORDER_BY_RANKING_QUERY()
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
def ORDER_BY_DETALHES_QUERY():
    return RETRABALHO_ORDER_BY_DETALHES_QUERY()
def ORDER_DIR_QUERY():
    return SORT_DIR_QUERY_ALIAS_ORDER_DIR_DESC()

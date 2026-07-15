from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.application.dto.refugos.refugos_registros_request import RefugosRegistrosRequest
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


FILIAL_QUERY = Query(
    ...,
    min_length=2,
    max_length=2,
    pattern="^(01|02)$",
    description='Filial Protheus ("01" = SC, "02" = ES).',
)
DATA_INICIO_QUERY = Query(
    None,
    alias="dataInicio",
    description="Data inicial (YYYY-MM-DD). Padrão: 1º dia do mês atual.",
)
DATA_FIM_QUERY = Query(
    None,
    alias="dataFim",
    description="Data final (YYYY-MM-DD). Padrão: hoje.",
)
DIMENSION_QUERY = Query(
    ...,
    pattern="^(motivo|materia_prima|produto_acabado|centro_trabalho|colaborador)$",
    description="Dimensão do ranking.",
)
MP_QUERY = Query(None, description="Filtro por código de matéria-prima.")
PA_QUERY = Query(None, description="Filtro por código de produto acabado.")
OP_QUERY = Query(None, description="Filtro por ordem de produção.")
MOTIVO_QUERY = Query(None, description="Filtro por código de motivo (CYO).")
RECURSO_QUERY = Query(
    None,
    alias="centroTrabalho",
    description="Filtro por centro de trabalho (BC_RECURSO).",
)
LIMIT_QUERY = Query(
    DEFAULT_RANKING_LIMIT,
    ge=1,
    le=MAX_RANKING_LIMIT,
    description="Quantidade máxima de itens no ranking.",
)
PAGE_QUERY = Query(DEFAULT_PAGE, ge=1, description="Página da listagem.")
PAGE_SIZE_QUERY = Query(
    DEFAULT_PAGE_SIZE,
    alias="pageSize",
    ge=1,
    le=MAX_PAGE_SIZE,
    description="Registros por página (máximo 100).",
)

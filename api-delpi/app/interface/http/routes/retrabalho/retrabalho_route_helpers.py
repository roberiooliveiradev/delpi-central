from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

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
    filial: str,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    recurso: Optional[str] = None,
    centro_custo: Optional[str] = None,
    codigo_operador: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
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


FILIAL_QUERY = Query(
    ...,
    min_length=2,
    max_length=2,
    pattern="^(01|02)$",
    description='Filial Protheus ("01" ou "02").',
)
DATA_INICIO_QUERY = Query(
    None,
    alias="dataInicio",
    description="Data inicial (YYYY-MM-DD). Padrão: últimos 12 meses.",
)
DATA_FIM_QUERY = Query(
    None,
    alias="dataFim",
    description="Data final (YYYY-MM-DD). Padrão: hoje.",
)
RECURSO_QUERY = Query(None, description="Filtro por recurso.")
CENTRO_CUSTO_QUERY = Query(None, alias="centroCusto", description="Filtro por centro de custo.")
CODIGO_OPERADOR_QUERY = Query(
    None,
    alias="codigoOperador",
    description="Filtro por código do operador.",
)
ORDER_BY_RANKING_QUERY = Query(
    "horas",
    alias="orderBy",
    pattern="^(horas|custo)$",
    description="Ordenação do ranking: horas ou custo.",
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
ORDER_BY_DETALHES_QUERY = Query(
    DEFAULT_SORT_BY,
    alias="orderBy",
    pattern="^(data|horas|custo)$",
    description="Ordenação dos detalhes: data, horas ou custo.",
)
ORDER_DIR_QUERY = Query(
    DEFAULT_SORT_DIR,
    alias="orderDir",
    pattern="^(asc|desc)$",
    description="Direção da ordenação: asc ou desc.",
)

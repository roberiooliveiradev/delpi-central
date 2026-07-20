from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.interface.http.query_param_enums import SORT_DIR_QUERY_DESC as SORT_DIR_QUERY

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_request import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    MAX_PAGE_SIZE,
    DespesasCentroCustoLancamentosRequest,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
    DespesasCentroCustoQueryRequest,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_despesas_centro_custo_query_request(
    *,
    start_date: str,
    end_date: str,
    branch: Optional[str] = None,
    cost_center: Optional[str] = None,
    supplier_code: Optional[str] = None,
    supplier_store: Optional[str] = None,
    limit: Optional[int] = None,
) -> DespesasCentroCustoQueryRequest:
    return DespesasCentroCustoQueryRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        limit=limit,
    )


def build_despesas_centro_custo_lancamentos_request(
    *,
    start_date: str,
    end_date: str,
    branch: Optional[str] = None,
    cost_center: Optional[str] = None,
    supplier_code: Optional[str] = None,
    supplier_store: Optional[str] = None,
    search: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort_by: str = DEFAULT_SORT_BY,
    sort_dir: str = DEFAULT_SORT_DIR,
) -> DespesasCentroCustoLancamentosRequest:
    return DespesasCentroCustoLancamentosRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


def execute_despesas_centro_custo_route(
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
            result.to_dict(),
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


PERIOD_START_QUERY = Query(
    ...,
    min_length=8,
    description="Data inicial (YYYY-MM-DD ou YYYYMMDD).",
)
PERIOD_END_QUERY = Query(
    ...,
    min_length=8,
    description="Data final (YYYY-MM-DD ou YYYYMMDD).",
)
BRANCH_QUERY = Query(
    None,
    min_length=2,
    max_length=2,
    pattern="^(01|02)$",
    description="Filial Protheus (01 ou 02).",
)
COST_CENTER_QUERY = Query(None, description="Centro de custo.")
SUPPLIER_CODE_QUERY = Query(None, description="Código do fornecedor.")
SUPPLIER_STORE_QUERY = Query(None, description="Loja do fornecedor.")
RANKING_LIMIT_QUERY = Query(
    DEFAULT_RANKING_LIMIT,
    ge=1,
    le=MAX_RANKING_LIMIT,
    description="Quantidade máxima de itens no ranking.",
)
PAGE_QUERY = Query(
    DEFAULT_PAGE,
    ge=1,
    description="Página da listagem (mínimo 1).",
)
PAGE_SIZE_QUERY = Query(
    DEFAULT_PAGE_SIZE,
    ge=1,
    le=MAX_PAGE_SIZE,
    description="Quantidade de registros por página (máximo 200).",
)
SEARCH_QUERY = Query(None, description="Busca textual em documento, pedido, produto, observações e fornecedor.")
SORT_BY_QUERY = Query(
    DEFAULT_SORT_BY,
    description="Campo de ordenação permitido.",
)
# SORT_DIR_QUERY imported from query_param_enums

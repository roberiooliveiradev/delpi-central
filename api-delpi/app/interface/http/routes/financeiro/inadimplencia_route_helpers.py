from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from app.application.dto.financeiro_inadimplencia.clientes_request import (
    InadimplenciaClientesRequest,
)
from app.application.dto.financeiro_inadimplencia.constantes import (
    DEFAULT_CLIENTES_SORT_BY,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_DIR,
    DEFAULT_TITULOS_SORT_BY,
    MAX_PAGE_SIZE,
)
from app.application.dto.financeiro_inadimplencia.mensal_request import (
    InadimplenciaMensalQueryRequest,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)
from app.application.dto.financeiro_inadimplencia.titulos_request import (
    InadimplenciaTitulosRequest,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def build_inadimplencia_query_request(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> InadimplenciaQueryRequest:
    return InadimplenciaQueryRequest.from_query(
        start_date=start_date,
        end_date=end_date,
    )


def build_inadimplencia_mensal_request(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    customer_code: Optional[str] = None,
    store_code: Optional[str] = None,
) -> InadimplenciaMensalQueryRequest:
    return InadimplenciaMensalQueryRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        customer_code=customer_code,
        store_code=store_code,
    )


def build_inadimplencia_clientes_request(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort_by: str = DEFAULT_CLIENTES_SORT_BY,
    sort_dir: str = DEFAULT_SORT_DIR,
    q: Optional[str] = None,
    only_with_delays: bool = True,
) -> InadimplenciaClientesRequest:
    return InadimplenciaClientesRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        q=q,
        only_with_delays=only_with_delays,
    )


def build_inadimplencia_titulos_request(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    customer_code: Optional[str] = None,
    store_code: Optional[str] = None,
    status: str = "all",
    delay_range: Optional[str] = None,
    q: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort_by: str = DEFAULT_TITULOS_SORT_BY,
    sort_dir: str = DEFAULT_SORT_DIR,
) -> InadimplenciaTitulosRequest:
    return InadimplenciaTitulosRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        customer_code=customer_code,
        store_code=store_code,
        status=status,
        delay_range=delay_range,
        q=q,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


def execute_inadimplencia_route(
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
    None,
    description=(
        "Data inicial inclusiva (YYYY-MM-DD). "
        "Omita com end_date para usar os últimos 12 meses completos."
    ),
)
PERIOD_END_QUERY = Query(
    None,
    description=(
        "Data final exclusiva (YYYY-MM-DD). "
        "Filtro: MES_REFERENCIA >= start_date AND MES_REFERENCIA < end_date."
    ),
)
PAGE_QUERY = Query(DEFAULT_PAGE, ge=1, description="Página (mínimo 1).")
PAGE_SIZE_QUERY = Query(
    DEFAULT_PAGE_SIZE,
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Tamanho da página (máximo {MAX_PAGE_SIZE}).",
)
SEARCH_QUERY = Query(None, description="Busca textual parametrizada.")
SORT_BY_QUERY = Query(None, description="Campo de ordenação permitido (whitelist).")
SORT_DIR_QUERY = Query(
    DEFAULT_SORT_DIR,
    pattern="^(asc|desc)$",
    description="Direção da ordenação: asc ou desc.",
)
ONLY_WITH_DELAYS_QUERY = Query(
    True,
    description="Se true, retorna apenas clientes com pelo menos um título em atraso.",
)
CUSTOMER_CODE_QUERY = Query(None, description="Código do cliente (CLIENTE).")
STORE_CODE_QUERY = Query(None, description="Loja do cliente (LOJA).")
STATUS_QUERY = Query(
    "all",
    pattern="^(all|on_time|late)$",
    description="Filtro de status: all, on_time ou late.",
)
DELAY_RANGE_QUERY = Query(
    None,
    description="Código oficial de FAIXA_ATRASO.",
)

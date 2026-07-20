from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.dto.financeiro_inadimplencia.constantes import (
    DEFAULT_CLIENTES_SORT_BY,
    DEFAULT_TITULOS_SORT_BY,
)
from app.application.security.api_delpi_permissions import (
    FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS,
)
from app.composition.financeiro_inadimplencia_composer import (
    build_get_inadimplencia_clientes_use_case,
    build_get_inadimplencia_faixas_atraso_use_case,
    build_get_inadimplencia_mensal_use_case,
    build_get_inadimplencia_resumo_use_case,
    build_get_inadimplencia_titulos_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.routes.financeiro.inadimplencia_route_helpers import (
    CUSTOMER_CODE_QUERY,
    CUSTOMERS_QUERY,
    DELAY_RANGE_QUERY,
    NOVOS_NEGOCIOS_QUERY,
    ONLY_WITH_DELAYS_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    PERIOD_END_QUERY,
    PERIOD_START_QUERY,
    SEARCH_QUERY,
    SORT_BY_QUERY,
    SORT_DIR_QUERY,
    STATUS_QUERY,
    STORE_CODE_QUERY,
    build_inadimplencia_clientes_request,
    build_inadimplencia_mensal_request,
    build_inadimplencia_query_request,
    build_inadimplencia_titulos_request,
    execute_inadimplencia_route,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/inadimplencia",
    tags=["Financeiro — Inadimplência"],
)


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inadimplencia_resumo",
        path="/financeiro/inadimplencia/resumo",
    ),
)
@require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)
def get_financeiro_inadimplencia_resumo_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
):
    try:
        request = build_inadimplencia_query_request(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar resumo de inadimplência: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_inadimplencia_route(
        use_case_builder=build_get_inadimplencia_resumo_use_case,
        request=request,
        operation_id="get_financeiro_inadimplencia_resumo",
        success_message="Resumo de inadimplência financeira carregado com sucesso.",
        error_context="carregar resumo de inadimplência financeira",
    )


@router.get(
    "/mensal",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inadimplencia_mensal",
        path="/financeiro/inadimplencia/mensal",
    ),
)
@require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)
def get_financeiro_inadimplencia_mensal_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    customer_code: Optional[str] = CUSTOMER_CODE_QUERY(),
    store_code: Optional[str] = STORE_CODE_QUERY(),
    customers: Optional[str] = CUSTOMERS_QUERY(),
    novos_negocios: bool = NOVOS_NEGOCIOS_QUERY(),
):
    try:
        request = build_inadimplencia_mensal_request(
            start_date=start_date,
            end_date=end_date,
            customer_code=customer_code,
            store_code=store_code,
            customers=customers,
            novos_negocios=novos_negocios,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar série mensal de inadimplência: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_inadimplencia_route(
        use_case_builder=build_get_inadimplencia_mensal_use_case,
        request=request,
        operation_id="get_financeiro_inadimplencia_mensal",
        success_message="Série mensal de inadimplência carregada com sucesso.",
        error_context="carregar série mensal de inadimplência",
    )


@router.get(
    "/faixas-atraso",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inadimplencia_faixas_atraso",
        path="/financeiro/inadimplencia/faixas-atraso",
    ),
)
@require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)
def get_financeiro_inadimplencia_faixas_atraso_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
):
    try:
        request = build_inadimplencia_query_request(
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar faixas de atraso: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_inadimplencia_route(
        use_case_builder=build_get_inadimplencia_faixas_atraso_use_case,
        request=request,
        operation_id="get_financeiro_inadimplencia_faixas_atraso",
        success_message="Faixas de atraso carregadas com sucesso.",
        error_context="carregar faixas de atraso",
    )


@router.get(
    "/clientes",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inadimplencia_clientes",
        path="/financeiro/inadimplencia/clientes",
    ),
)
@require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)
def get_financeiro_inadimplencia_clientes_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
    sort_by: Optional[str] = SORT_BY_QUERY(),
    sort_dir: str = SORT_DIR_QUERY(),
    q: Optional[str] = SEARCH_QUERY(),
    only_with_delays: bool = ONLY_WITH_DELAYS_QUERY(),
):
    try:
        request = build_inadimplencia_clientes_request(
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by or DEFAULT_CLIENTES_SORT_BY,
            sort_dir=sort_dir,
            q=q,
            only_with_delays=only_with_delays,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar ranking de clientes: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_inadimplencia_route(
        use_case_builder=build_get_inadimplencia_clientes_use_case,
        request=request,
        operation_id="get_financeiro_inadimplencia_clientes",
        success_message="Ranking de clientes por inadimplência carregado com sucesso.",
        error_context="carregar ranking de clientes por inadimplência",
    )


@router.get(
    "/titulos",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_inadimplencia_titulos",
        path="/financeiro/inadimplencia/titulos",
    ),
)
@require_any_permission(FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS)
def get_financeiro_inadimplencia_titulos_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    customer_code: Optional[str] = CUSTOMER_CODE_QUERY(),
    store_code: Optional[str] = STORE_CODE_QUERY(),
    status: str = STATUS_QUERY(),
    delay_range: Optional[str] = DELAY_RANGE_QUERY(),
    q: Optional[str] = SEARCH_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
    sort_by: Optional[str] = SORT_BY_QUERY(),
    sort_dir: str = SORT_DIR_QUERY(),
):
    try:
        request = build_inadimplencia_titulos_request(
            start_date=start_date,
            end_date=end_date,
            customer_code=customer_code,
            store_code=store_code,
            status=status,
            delay_range=delay_range,
            q=q,
            page=page,
            page_size=page_size,
            sort_by=sort_by or DEFAULT_TITULOS_SORT_BY,
            sort_dir=sort_dir,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar títulos de inadimplência: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_inadimplencia_route(
        use_case_builder=build_get_inadimplencia_titulos_use_case,
        request=request,
        operation_id="get_financeiro_inadimplencia_titulos",
        success_message="Títulos de inadimplência carregados com sucesso.",
        error_context="carregar títulos de inadimplência",
    )

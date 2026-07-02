from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.dto.financeiro_despesas_centro_custo.period_filter_request import (
    PeriodFilterRequest,
)
from app.application.security.api_delpi_permissions import (
    FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS,
)
from app.composition.financeiro_despesas_centro_custo_composer import (
    build_get_despesas_centro_custo_filtros_use_case,
    build_get_despesas_centro_custo_lancamentos_use_case,
    build_get_despesas_centro_custo_ranking_centros_use_case,
    build_get_despesas_centro_custo_ranking_fornecedores_use_case,
    build_get_despesas_centro_custo_resumo_use_case,
    build_get_despesas_centro_custo_serie_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.despesas_centro_custo_route_helpers import (
    BRANCH_QUERY,
    COST_CENTER_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    PERIOD_END_QUERY,
    PERIOD_START_QUERY,
    RANKING_LIMIT_QUERY,
    SEARCH_QUERY,
    SORT_BY_QUERY,
    SORT_DIR_QUERY,
    SUPPLIER_CODE_QUERY,
    SUPPLIER_STORE_QUERY,
    build_despesas_centro_custo_lancamentos_request,
    build_despesas_centro_custo_query_request,
    execute_despesas_centro_custo_route,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/despesas-centro-custo",
    tags=["Financeiro — Despesas por Centro de Custo"],
)


@router.get(
    "/filtros",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_filtros",
        path="/financeiro/despesas-centro-custo/filtros",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_filtros_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    cost_center: Optional[str] = COST_CENTER_QUERY,
):
    try:
        request = build_despesas_centro_custo_query_request(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
        )
        use_case = build_get_despesas_centro_custo_filtros_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_financeiro_despesas_centro_custo_filtros",
            message="Filtros de despesas por centro de custo carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao carregar filtros de despesas CC: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar filtros de despesas por centro de custo: {exc}")
        return error_response(
            "Erro interno ao carregar filtros de despesas por centro de custo.",
            status_code=500,
        )


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_resumo",
        path="/financeiro/despesas-centro-custo/resumo",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_resumo_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    cost_center: Optional[str] = COST_CENTER_QUERY,
    supplier_code: Optional[str] = SUPPLIER_CODE_QUERY,
    supplier_store: Optional[str] = SUPPLIER_STORE_QUERY,
):
    request = build_despesas_centro_custo_query_request(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
    )
    return execute_despesas_centro_custo_route(
        use_case_builder=build_get_despesas_centro_custo_resumo_use_case,
        request=request,
        operation_id="get_financeiro_despesas_centro_custo_resumo",
        success_message="Resumo de despesas por centro de custo carregado com sucesso.",
        error_context="carregar resumo de despesas por centro de custo",
    )


@router.get(
    "/serie",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_serie",
        path="/financeiro/despesas-centro-custo/serie",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_serie_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    cost_center: Optional[str] = COST_CENTER_QUERY,
    supplier_code: Optional[str] = SUPPLIER_CODE_QUERY,
    supplier_store: Optional[str] = SUPPLIER_STORE_QUERY,
):
    request = build_despesas_centro_custo_query_request(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
    )
    return execute_despesas_centro_custo_route(
        use_case_builder=build_get_despesas_centro_custo_serie_use_case,
        request=request,
        operation_id="get_financeiro_despesas_centro_custo_serie",
        success_message="Série mensal de despesas carregada com sucesso.",
        error_context="carregar série mensal de despesas por centro de custo",
    )


@router.get(
    "/ranking-centros",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_ranking_centros",
        path="/financeiro/despesas-centro-custo/ranking-centros",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_ranking_centros_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    supplier_code: Optional[str] = SUPPLIER_CODE_QUERY,
    supplier_store: Optional[str] = SUPPLIER_STORE_QUERY,
    limit: int = RANKING_LIMIT_QUERY,
):
    request = build_despesas_centro_custo_query_request(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        limit=limit,
    )
    return execute_despesas_centro_custo_route(
        use_case_builder=build_get_despesas_centro_custo_ranking_centros_use_case,
        request=request,
        operation_id="get_financeiro_despesas_centro_custo_ranking_centros",
        success_message="Ranking de centros de custo carregado com sucesso.",
        error_context="carregar ranking de centros de custo",
    )


@router.get(
    "/ranking-fornecedores",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_ranking_fornecedores",
        path="/financeiro/despesas-centro-custo/ranking-fornecedores",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_ranking_fornecedores_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    cost_center: Optional[str] = COST_CENTER_QUERY,
    limit: int = RANKING_LIMIT_QUERY,
):
    """Ranking de fornecedores — aceita branch e cost_center (sem supplier_code/store)."""
    request = build_despesas_centro_custo_query_request(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        limit=limit,
    )
    return execute_despesas_centro_custo_route(
        use_case_builder=build_get_despesas_centro_custo_ranking_fornecedores_use_case,
        request=request,
        operation_id="get_financeiro_despesas_centro_custo_ranking_fornecedores",
        success_message="Ranking de fornecedores carregado com sucesso.",
        error_context="carregar ranking de fornecedores",
    )


@router.get(
    "/lancamentos",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_despesas_centro_custo_lancamentos",
        path="/financeiro/despesas-centro-custo/lancamentos",
    ),
)
@require_any_permission(FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS)
def get_financeiro_despesas_centro_custo_lancamentos_route(
    start_date: str = PERIOD_START_QUERY,
    end_date: str = PERIOD_END_QUERY,
    branch: Optional[str] = BRANCH_QUERY,
    cost_center: Optional[str] = COST_CENTER_QUERY,
    supplier_code: Optional[str] = SUPPLIER_CODE_QUERY,
    supplier_store: Optional[str] = SUPPLIER_STORE_QUERY,
    search: Optional[str] = SEARCH_QUERY,
    page: int = PAGE_QUERY,
    page_size: int = PAGE_SIZE_QUERY,
    sort_by: str = SORT_BY_QUERY,
    sort_dir: str = SORT_DIR_QUERY,
):
    try:
        request = build_despesas_centro_custo_lancamentos_request(
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
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar lançamentos de despesas CC: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_despesas_centro_custo_route(
        use_case_builder=build_get_despesas_centro_custo_lancamentos_use_case,
        request=request,
        operation_id="get_financeiro_despesas_centro_custo_lancamentos",
        success_message="Lançamentos de despesas por centro de custo carregados com sucesso.",
        error_context="carregar lançamentos de despesas por centro de custo",
    )

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import CONTROLE_RETRABALHO_READ_PERMISSIONS
from app.composition.retrabalho_composer import (
    build_get_retrabalho_colaboradores_use_case,
    build_get_retrabalho_detalhes_use_case,
    build_get_retrabalho_filtros_use_case,
    build_get_retrabalho_health_use_case,
    build_get_retrabalho_mensal_use_case,
    build_get_retrabalho_recursos_use_case,
    build_get_retrabalho_resumo_use_case,
    build_get_retrabalho_rework_cost_pct_use_case,
)
from app.core.responses import error_response
from app.interface.http.kpi_field_labels import (
    RETRABALHO_REWORK_COST_PCT_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.retrabalho.retrabalho_route_helpers import (
    CENTRO_CUSTO_QUERY,
    CODIGO_OPERADOR_QUERY,
    DATA_FIM_QUERY,
    DATA_INICIO_QUERY,
    FILIAL_QUERY,
    LIMIT_QUERY,
    ORDER_BY_DETALHES_QUERY,
    ORDER_BY_RANKING_QUERY,
    ORDER_DIR_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    RECURSO_QUERY,
    build_retrabalho_detalhes_request,
    build_retrabalho_query_request,
    execute_retrabalho_route,
)
from app.interface.http.routes.retrabalho.retrabalho_branch_access import branch_access_error
from app.utils.logger import log_error

router = APIRouter(
    prefix="/retrabalhos",
    tags=["Qualidade — Controle de Retrabalhos"],
)


@router.get(
    "/health",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_health",
        path="/retrabalhos/health",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_health_route():
    try:
        use_case = build_get_retrabalho_health_use_case()
        result = use_case.execute()
        return api_delpi_success(
            result,
            operation_id="get_retrabalhos_health",
            message="Health check de retrabalhos executado com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro no health check de retrabalhos: {exc}")
        return error_response(
            "Erro interno no health check de retrabalhos.",
            status_code=500,
        )


@router.get(
    "/filtros",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_filtros",
        path="/retrabalhos/filtros",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_filtros_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar filtros de retrabalhos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_filtros_use_case,
        request=request,
        operation_id="get_retrabalhos_filtros",
        success_message="Filtros de retrabalhos carregados com sucesso.",
        error_context="carregar filtros de retrabalhos",
    )


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_resumo",
        path="/retrabalhos/resumo",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_resumo_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar resumo de retrabalhos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_resumo_use_case,
        request=request,
        operation_id="get_retrabalhos_resumo",
        success_message="Resumo de retrabalhos carregado com sucesso.",
        error_context="carregar resumo de retrabalhos",
    )


@router.get(
    "/rework_cost_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_rework_cost_pct",
        path="/retrabalhos/rework_cost_pct",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_rework_cost_pct(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar rework cost / ROL: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_retrabalho_rework_cost_pct_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_retrabalhos_rework_cost_pct",
            message="Custo de retrabalho / ROL carregado com sucesso.",
            fields=kpi_fields(RETRABALHO_REWORK_COST_PCT_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar rework cost / ROL: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar rework cost / ROL: {exc}")
        return error_response(
            "Erro interno ao carregar custo de retrabalho / ROL.",
            status_code=500,
        )


@router.get(
    "/mensal",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_mensal",
        path="/retrabalhos/mensal",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_mensal_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar série mensal de retrabalhos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_mensal_use_case,
        request=request,
        operation_id="get_retrabalhos_mensal",
        success_message="Série mensal de retrabalhos carregada com sucesso.",
        error_context="carregar série mensal de retrabalhos",
    )


@router.get(
    "/recursos",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_recursos",
        path="/retrabalhos/recursos",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_recursos_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
    order_by: str = ORDER_BY_RANKING_QUERY(),
    limit: int = LIMIT_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
            order_by=order_by,
            limit=limit,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar ranking de recursos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_recursos_use_case,
        request=request,
        operation_id="get_retrabalhos_recursos",
        success_message="Ranking de recursos de retrabalhos carregado com sucesso.",
        error_context="carregar ranking de recursos de retrabalhos",
    )


@router.get(
    "/colaboradores",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_colaboradores",
        path="/retrabalhos/colaboradores",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_colaboradores_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
    order_by: str = ORDER_BY_RANKING_QUERY(),
    limit: int = LIMIT_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
            order_by=order_by,
            limit=limit,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar ranking de colaboradores: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_colaboradores_use_case,
        request=request,
        operation_id="get_retrabalhos_colaboradores",
        success_message="Ranking de colaboradores de retrabalhos carregado com sucesso.",
        error_context="carregar ranking de colaboradores de retrabalhos",
    )


@router.get(
    "/detalhes",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_retrabalhos_detalhes",
        path="/retrabalhos/detalhes",
    ),
)
@require_any_permission(CONTROLE_RETRABALHO_READ_PERMISSIONS)
def get_retrabalhos_detalhes_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    centro_custo: Optional[str] = CENTRO_CUSTO_QUERY(),
    codigo_operador: Optional[str] = CODIGO_OPERADOR_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
    order_by: str = ORDER_BY_DETALHES_QUERY(),
    order_dir: str = ORDER_DIR_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_retrabalho_detalhes_request(
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
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar detalhes de retrabalhos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_retrabalho_route(
        use_case_builder=build_get_retrabalho_detalhes_use_case,
        request=request,
        operation_id="get_retrabalhos_detalhes",
        success_message="Detalhes de retrabalhos carregados com sucesso.",
        error_context="carregar detalhes de retrabalhos",
    )

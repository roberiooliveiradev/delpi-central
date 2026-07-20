from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import SCRAP_MONITORING_READ_PERMISSIONS
from app.composition.refugos_composer import (
    build_get_refugos_filtros_use_case,
    build_get_refugos_health_use_case,
    build_get_refugos_rankings_use_case,
    build_get_refugos_registros_use_case,
    build_get_refugos_resumo_use_case,
    build_get_refugos_serie_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.routes.refugos.refugos_branch_access import branch_access_error
from app.interface.http.routes.refugos.refugos_route_helpers import (
    DATA_FIM_QUERY,
    DATA_INICIO_QUERY,
    DIMENSION_QUERY,
    FILIAL_QUERY,
    GRANULARITY_QUERY,
    LIMIT_QUERY,
    MOTIVO_QUERY,
    MP_QUERY,
    OP_QUERY,
    PA_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    RECURSO_QUERY,
    build_refugos_query_request,
    build_refugos_registros_request,
    build_refugos_serie_request,
    execute_refugos_route,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/refugos",
    tags=["Produção — Acompanhamento de Refugos"],
)


@router.get(
    "/health",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_health",
        path="/refugos/health",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_health_route():
    return execute_refugos_route(
        use_case_builder=build_get_refugos_health_use_case,
        request=None,
        operation_id="get_refugos_health",
        success_message="Health check de refugos executado com sucesso.",
        error_context="executar health check de refugos",
    )


@router.get(
    "/filtros",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_filtros",
        path="/refugos/filtros",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_filtros_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_refugos_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar filtros de refugos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_refugos_route(
        use_case_builder=build_get_refugos_filtros_use_case,
        request=request,
        operation_id="get_refugos_filtros",
        success_message="Filtros de refugos carregados com sucesso.",
        error_context="carregar filtros de refugos",
    )


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_resumo",
        path="/refugos/resumo",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_resumo_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    mp: Optional[str] = MP_QUERY(),
    pa: Optional[str] = PA_QUERY(),
    op: Optional[str] = OP_QUERY(),
    motivo: Optional[str] = MOTIVO_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_refugos_query_request(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar resumo de refugos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_refugos_route(
        use_case_builder=build_get_refugos_resumo_use_case,
        request=request,
        operation_id="get_refugos_resumo",
        success_message="Resumo de refugos carregado com sucesso.",
        error_context="carregar resumo de refugos",
    )


@router.get(
    "/rankings",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_rankings",
        path="/refugos/rankings",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_rankings_route(
    filial: str = FILIAL_QUERY(),
    dimension: str = DIMENSION_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    mp: Optional[str] = MP_QUERY(),
    pa: Optional[str] = PA_QUERY(),
    op: Optional[str] = OP_QUERY(),
    motivo: Optional[str] = MOTIVO_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    limit: int = LIMIT_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_refugos_query_request(
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
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar rankings de refugos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_refugos_route(
        use_case_builder=build_get_refugos_rankings_use_case,
        request=request,
        operation_id="get_refugos_rankings",
        success_message="Ranking de refugos carregado com sucesso.",
        error_context="carregar ranking de refugos",
    )


@router.get(
    "/serie",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_serie",
        path="/refugos/serie",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_serie_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    granularity: Optional[str] = GRANULARITY_QUERY(),
    mp: Optional[str] = MP_QUERY(),
    pa: Optional[str] = PA_QUERY(),
    op: Optional[str] = OP_QUERY(),
    motivo: Optional[str] = MOTIVO_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_refugos_serie_request(
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
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar série de refugos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_refugos_route(
        use_case_builder=build_get_refugos_serie_use_case,
        request=request,
        operation_id="get_refugos_serie",
        success_message="Série temporal de refugos carregada com sucesso.",
        error_context="carregar série temporal de refugos",
    )


@router.get(
    "/registros",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_refugos_registros",
        path="/refugos/registros",
    ),
)
@require_any_permission(SCRAP_MONITORING_READ_PERMISSIONS)
def get_refugos_registros_route(
    filial: str = FILIAL_QUERY(),
    data_inicio: Optional[str] = DATA_INICIO_QUERY(),
    data_fim: Optional[str] = DATA_FIM_QUERY(),
    mp: Optional[str] = MP_QUERY(),
    pa: Optional[str] = PA_QUERY(),
    op: Optional[str] = OP_QUERY(),
    motivo: Optional[str] = MOTIVO_QUERY(),
    recurso: Optional[str] = RECURSO_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
):
    filial_error = branch_access_error(filial)
    if filial_error:
        return filial_error

    try:
        request = build_refugos_registros_request(
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
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar registros de refugos: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_refugos_route(
        use_case_builder=build_get_refugos_registros_use_case,
        request=request,
        operation_id="get_refugos_registros",
        success_message="Registros de refugos carregados com sucesso.",
        error_context="carregar registros de refugos",
    )

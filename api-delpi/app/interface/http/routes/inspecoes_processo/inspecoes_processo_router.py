from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    INSPECOES_PROCESSO_BRANCH_VIEW_PERMS,
    INSPECOES_PROCESSO_READ_PERMISSIONS,
    INSPECOES_PROCESSO_VIEW,
)
from app.composition.inspecoes_processo_composer import (
    build_get_inspecoes_processo_historico_detalhe_use_case,
    build_get_inspecoes_processo_resumo_use_case,
    build_list_inspecoes_processo_auditoria_apontamentos_use_case,
    build_list_inspecoes_processo_historico_use_case,
    build_list_inspecoes_processo_por_ensaiador_use_case,
    build_list_inspecoes_processo_por_operacao_use_case,
    build_list_inspecoes_processo_por_produto_use_case,
    build_list_inspecoes_processo_ranking_ensaio_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    INSPECTION_RESULT_QUERY,
)

router = APIRouter(
    prefix="/inspecoes-processo",
    tags=["Inspeções de Processo"],
)


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def _branch_view_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True

    user = get_current_user()
    if user is None:
        return False

    if has_permission(user, INSPECOES_PROCESSO_VIEW):
        return True

    branch_perm = INSPECOES_PROCESSO_BRANCH_VIEW_PERMS.get(branch)
    return branch_perm is not None and has_permission(user, branch_perm)


def _branch_access_error(branch: str):
    if _branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar inspeções de processo desta filial.",
        status_code=403,
    )


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_resumo",
        path="/inspecoes-processo/resumo",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_resumo_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_inspecoes_processo_resumo_use_case()
        result = use_case.execute(branch=branch)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_processo_resumo",
            message="Resumo de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no resumo de inspeções de processo: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar resumo de inspeções de processo: {exc}")
        return error_response(
            "Erro interno ao carregar resumo de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/ranking-ensaio",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_ranking_ensaio",
        path="/inspecoes-processo/ranking-ensaio",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_ranking_ensaio_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    limit: int = Query(default=10, ge=1, le=50),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_ranking_ensaio_use_case()
        items = use_case.execute(branch=branch, limit=limit)

        return api_delpi_success(
            [item.to_dict() for item in items],
            operation_id="get_inspecoes_processo_ranking_ensaio",
            message="Ranking de ensaios de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no ranking de ensaio de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(
            f"Erro ao carregar ranking de ensaio de inspeções de processo: {exc}"
        )
        return error_response(
            "Erro interno ao carregar ranking de ensaio de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/por-produto",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_por_produto",
        path="/inspecoes-processo/por-produto",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_por_produto_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    limit: int = Query(default=10, ge=1, le=50),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_por_produto_use_case()
        items = use_case.execute(branch=branch, limit=limit)

        return api_delpi_success(
            [item.to_dict() for item in items],
            operation_id="get_inspecoes_processo_por_produto",
            message="Ranking por produto de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no ranking por produto de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(
            f"Erro ao carregar ranking por produto de inspeções de processo: {exc}"
        )
        return error_response(
            "Erro interno ao carregar ranking por produto de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/por-operacao",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_por_operacao",
        path="/inspecoes-processo/por-operacao",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_por_operacao_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    limit: int = Query(default=10, ge=1, le=50),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_por_operacao_use_case()
        items = use_case.execute(branch=branch, limit=limit)

        return api_delpi_success(
            [item.to_dict() for item in items],
            operation_id="get_inspecoes_processo_por_operacao",
            message="Ranking por operação de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no ranking por operação de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(
            f"Erro ao carregar ranking por operação de inspeções de processo: {exc}"
        )
        return error_response(
            "Erro interno ao carregar ranking por operação de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/por-ensaiador",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_por_ensaiador",
        path="/inspecoes-processo/por-ensaiador",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_por_ensaiador_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    limit: int = Query(default=10, ge=1, le=50),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_por_ensaiador_use_case()
        items = use_case.execute(branch=branch, limit=limit)

        return api_delpi_success(
            [item.to_dict() for item in items],
            operation_id="get_inspecoes_processo_por_ensaiador",
            message="Ranking por ensaiador de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no ranking por ensaiador de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(
            f"Erro ao carregar ranking por ensaiador de inspeções de processo: {exc}"
        )
        return error_response(
            "Erro interno ao carregar ranking por ensaiador de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/historico",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_historico",
        path="/inspecoes-processo/historico",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_historico_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=50),
    ordem_producao: str | None = Query(default=None),
    codigo_produto: str | None = Query(default=None),
    resultado: str | None = INSPECTION_RESULT_QUERY(),
    data_inicio: str | None = Query(default=None),
    data_fim: str | None = Query(default=None),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_historico_use_case()
        result = use_case.execute(
            branch=branch,
            page=page,
            page_size=page_size,
            ordem_producao=ordem_producao,
            codigo_produto=codigo_produto,
            resultado=resultado,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_processo_historico",
            message="Histórico de inspeções de processo carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no histórico de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar histórico de inspeções de processo: {exc}")
        detail = str(exc).lower()
        if "hyt00" in detail or "timeout" in detail:
            return error_response(
                "A consulta do histórico demorou demais. Refine os filtros "
                "(produto ou ordem de produção) e tente novamente.",
                status_code=504,
            )
        return error_response(
            "Erro interno ao carregar histórico de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/historico/detalhe",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_historico_detalhe",
        path="/inspecoes-processo/historico/detalhe",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_historico_detalhe_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    ordem_producao: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_inspecoes_processo_historico_detalhe_use_case()
        result = use_case.execute(
            branch=branch,
            ordem_producao=ordem_producao,
            page=page,
            page_size=page_size,
        )

        if result is None:
            return not_found_response(
                "Ordem de produção não encontrada para a filial informada.",
                code="OP_NOT_FOUND",
            )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_processo_historico_detalhe",
            message="Detalhe da ordem de produção carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação no detalhe de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar detalhe de inspeções de processo: {exc}")
        detail = str(exc).lower()
        if "hyt00" in detail or "timeout" in detail:
            return error_response(
                "A consulta do detalhe demorou demais. Tente novamente em instantes.",
                status_code=504,
            )
        return error_response(
            "Erro interno ao carregar detalhe de inspeções de processo.",
            status_code=500,
        )


@router.get(
    "/auditoria-apontamentos",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_processo_auditoria_apontamentos",
        path="/inspecoes-processo/auditoria-apontamentos",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_inspecoes_processo_auditoria_apontamentos_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    data: str | None = Query(
        default=None,
        description="Data de produção (YYYY-MM-DD). Default: hoje.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_processo_auditoria_apontamentos_use_case()
        result = use_case.execute(
            branch=branch,
            data=data,
            page=page,
            page_size=page_size,
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_processo_auditoria_apontamentos",
            message="Auditoria de apontamentos sem inspeção carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação na auditoria de apontamentos de inspeções de processo: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(
            f"Erro ao carregar auditoria de apontamentos de inspeções de processo: {exc}"
        )
        detail = str(exc).lower()
        if "hyt00" in detail or "timeout" in detail:
            return error_response(
                "A consulta da auditoria demorou demais. Tente outra data ou filial.",
                status_code=504,
            )
        return error_response(
            "Erro interno ao carregar auditoria de apontamentos de inspeções de processo.",
            status_code=500,
        )

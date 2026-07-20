from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    INSPECOES_ENTRADA_BRANCH_VIEW_PERMS,
    INSPECOES_ENTRADA_READ_PERMISSIONS,
    INSPECOES_ENTRADA_VIEW,
)
from app.composition.inspecoes_entrada_composer import (
    build_get_inspecoes_entrada_historico_detalhe_use_case,
    build_get_inspecoes_entrada_resumo_use_case,
    build_list_inspecoes_entrada_historico_use_case,
    build_list_inspecoes_entrada_pendentes_fornecedor_use_case,
    build_list_inspecoes_entrada_pendentes_use_case,
    build_list_inspecoes_entrada_rejeitadas_ensaiador_use_case,
    build_list_inspecoes_entrada_rejeitadas_produto_use_case,
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
    prefix="/inspecoes-entrada",
    tags=["Inspeções de Entrada"],
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

    if has_permission(user, INSPECOES_ENTRADA_VIEW):
        return True

    branch_perm = INSPECOES_ENTRADA_BRANCH_VIEW_PERMS.get(branch)
    return branch_perm is not None and has_permission(user, branch_perm)


def _branch_access_error(branch: str):
    if _branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar inspeções de entrada desta filial.",
        status_code=403,
    )


@router.get(
    "/resumo",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_resumo",
        path="/inspecoes-entrada/resumo",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_resumo_route(
    branch: str = BRANCH_QUERY_REQUIRED,
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_inspecoes_entrada_resumo_use_case()
        result = use_case.execute(branch=branch)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_resumo",
            message="Resumo de inspeções de entrada carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no resumo de inspeções de entrada: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar resumo de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar resumo de inspeções de entrada.",
            status_code=500,
        )


@router.get(
    "/pendentes",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_pendentes",
        path="/inspecoes-entrada/pendentes",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_pendentes_route(
    branch: str = BRANCH_QUERY_REQUIRED,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_entrada_pendentes_use_case()
        result = use_case.execute(
            branch=branch,
            page=page,
            page_size=page_size,
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_pendentes",
            message="Inspeções pendentes carregadas com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação nas inspeções pendentes de entrada: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar inspeções pendentes de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar inspeções pendentes de entrada.",
            status_code=500,
        )


@router.get(
    "/pendentes-fornecedor",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_pendentes_fornecedor",
        path="/inspecoes-entrada/pendentes-fornecedor",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_pendentes_fornecedor_route(
    branch: str = BRANCH_QUERY_REQUIRED,
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_entrada_pendentes_fornecedor_use_case()
        result = use_case.execute(branch=branch)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_pendentes_fornecedor",
            message="Pendências por fornecedor carregadas com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação nas pendências por fornecedor de inspeções de entrada: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar pendências por fornecedor de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar pendências por fornecedor de inspeções de entrada.",
            status_code=500,
        )


@router.get(
    "/rejeitadas-ensaiador",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_rejeitadas_ensaiador",
        path="/inspecoes-entrada/rejeitadas-ensaiador",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_rejeitadas_ensaiador_route(
    branch: str = BRANCH_QUERY_REQUIRED,
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_entrada_rejeitadas_ensaiador_use_case()
        result = use_case.execute(branch=branch)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_rejeitadas_ensaiador",
            message="Rejeitadas por ensaiador carregadas com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação nas rejeitadas por ensaiador de inspeções de entrada: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar rejeitadas por ensaiador de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar rejeitadas por ensaiador de inspeções de entrada.",
            status_code=500,
        )


@router.get(
    "/rejeitadas-produto",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_rejeitadas_produto",
        path="/inspecoes-entrada/rejeitadas-produto",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_rejeitadas_produto_route(
    branch: str = BRANCH_QUERY_REQUIRED,
    limit: int = Query(default=50, ge=1, le=200),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_entrada_rejeitadas_produto_use_case()
        result = use_case.execute(branch=branch, limit=limit)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_rejeitadas_produto",
            message="Rejeições por produto carregadas com sucesso.",
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação nas rejeições por produto de inspeções de entrada: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar rejeições por produto de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar rejeições por produto de inspeções de entrada.",
            status_code=500,
        )


@router.get(
    "/historico",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_historico",
        path="/inspecoes-entrada/historico",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_historico_route(
    branch: str = BRANCH_QUERY_REQUIRED,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    result: str | None = INSPECTION_RESULT_QUERY,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    product_code: str | None = Query(default=None),
    inspector: str | None = Query(default=None),
    invoice_number: str | None = Query(default=None),
    lot: str | None = Query(default=None),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_inspecoes_entrada_historico_use_case()
        payload = use_case.execute(
            branch=branch,
            page=page,
            page_size=page_size,
            result=result,
            date_from=date_from,
            date_to=date_to,
            supplier=supplier,
            product_code=product_code,
            inspector=inspector,
            invoice_number=invoice_number,
            lot=lot,
        )

        return api_delpi_success(
            payload.to_dict(),
            operation_id="get_inspecoes_entrada_historico",
            message="Histórico de inspeções carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no histórico de inspeções de entrada: {exc}")
        return error_response(str(exc), status_code=422)

    except Exception as exc:
        log_error(f"Erro ao carregar histórico de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar histórico de inspeções de entrada.",
            status_code=500,
        )


@router.get(
    "/historico/detalhe",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_inspecoes_entrada_historico_detalhe",
        path="/inspecoes-entrada/historico/detalhe",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def get_inspecoes_entrada_historico_detalhe_route(
    branch: str = BRANCH_QUERY_REQUIRED,
    inspection_id: str = Query(..., min_length=1),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_inspecoes_entrada_historico_detalhe_use_case()
        result = use_case.execute(branch=branch, inspection_id=inspection_id)

        if result is None:
            return not_found_response(
                "Inspeção não encontrada para a filial informada.",
                code="INSPECAO_NOT_FOUND",
            )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_inspecoes_entrada_historico_detalhe",
            message="Detalhe da inspeção carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no detalhe de inspeções de entrada: {exc}")
        return error_response(str(exc), status_code=422)

    except Exception as exc:
        log_error(f"Erro ao carregar detalhe de inspeções de entrada: {exc}")
        return error_response(
            "Erro interno ao carregar detalhe de inspeções de entrada.",
            status_code=500,
        )

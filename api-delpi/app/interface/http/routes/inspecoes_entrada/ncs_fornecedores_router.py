"""Consulta de NCs de fornecedor no contexto de Inspecoes de Entrada.

Reutiliza o mesmo caso de uso TOTVS QI2 da Qualidade, mas exige a
permissao e a filial do plugin de recebimento. O filtro type=supplier
e definido no servidor e nao pode ser ampliado pelo cliente.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_any_permission

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.application.security.api_delpi_permissions import (
    INSPECOES_ENTRADA_READ_PERMISSIONS,
)
from app.composition.quality_composer import build_list_nonconformity_use_case
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.period_query_params import END_DATE_QUERY, START_DATE_QUERY
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    NONCONFORMITY_QI2_STATUS_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.inspecoes_entrada.inspecoes_entrada_branch_access import (
    branch_access_error,
)
from app.utils.logger import log_error

router = APIRouter()


@router.get(
    "/ncs-fornecedores",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_inspecoes_entrada_ncs_fornecedores",
        path="/inspecoes-entrada/ncs-fornecedores",
    ),
)
@require_any_permission(INSPECOES_ENTRADA_READ_PERMISSIONS)
def list_inspecoes_entrada_ncs_fornecedores_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    start_date: str | None = START_DATE_QUERY(),
    end_date: str | None = END_DATE_QUERY(),
    status: str | None = NONCONFORMITY_QI2_STATUS_QUERY(),
    item_code: str | None = Query(default=None, max_length=50),
    description: str | None = Query(default=None, max_length=160),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
):
    """Lista somente QI2_TIPO=3, respeitando RBAC por filial do recebimento."""
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = ListNonconformityRequest(
            type="supplier",
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            status=status,
            item_code=item_code,
            description=description,
            page=page,
            page_size=page_size,
        )
        result = build_list_nonconformity_use_case().execute(request)
        return api_delpi_success(
            result.to_dict(),
            operation_id="list_inspecoes_entrada_ncs_fornecedores",
            message="NCs de fornecedores carregadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Filtro invalido de NC de fornecedor (entrada): {exc}")
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao listar NCs de fornecedor (entrada): {exc}")
        return error_response(
            "Erro interno ao carregar NCs de fornecedores.",
            status_code=500,
        )

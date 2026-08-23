from __future__ import annotations

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import SAFETY_STOCK_READ_PERMISSIONS
from app.composition.supplies_composer import (
    build_get_purchase_requests_open_coverage_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_REQUIRED
from app.interface.http.routes.supplies.safety_stock_branch_access import (
    branch_access_error,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/purchase-requests",
    tags=["Suprimentos — Solicitações de compra"],
)


@router.get(
    "/open-coverage",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_purchase_requests_open_coverage",
        path="/supplies/purchase-requests/open-coverage",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_purchase_requests_open_coverage_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_purchase_requests_open_coverage_use_case()
        result = use_case.execute(branch=branch)
        return api_delpi_success(
            result,
            operation_id="get_supplies_purchase_requests_open_coverage",
            message="Cobertura das solicitações de compra em aberto carregada com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar cobertura de solicitações: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao carregar cobertura de solicitações: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para as solicitações de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao carregar cobertura de solicitações de compra: {exc}")
        return error_response(
            "Erro interno ao carregar cobertura das solicitações de compra em aberto.",
            status_code=500,
        )

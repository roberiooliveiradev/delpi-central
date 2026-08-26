from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission, require_auth

from app.application.security.api_delpi_permissions import (
    PURCHASE_REQUESTS_READ_PERMISSIONS,
    SAFETY_STOCK_READ_PERMISSIONS,
)
from app.composition.supplies_composer import (
    build_get_purchase_requests_open_coverage_use_case,
    build_get_supplies_purchase_request_lines_use_case,
    build_list_supplies_purchase_request_lines_use_case,
    build_list_supplies_purchase_request_recent_linked_orders_use_case,
    build_list_supplies_purchase_request_requesters_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_REQUIRED
from app.interface.http.routes.supplies.purchase_requests_branch_access import (
    branch_access_error as purchase_requests_branch_access_error,
)
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


@router.get(
    "/lines",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_purchase_request_lines",
        path="/supplies/purchase-requests/lines",
    ),
)
@require_any_permission(PURCHASE_REQUESTS_READ_PERMISSIONS)
def list_supplies_purchase_request_lines_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    cost_centers: Annotated[list[str] | None, Query()] = None,
    request_number: str | None = Query(None),
    requester_protheus_user_id: Annotated[list[str] | None, Query()] = None,
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    order_number: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    branch_error = purchase_requests_branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_supplies_purchase_request_lines_use_case()
        result = use_case.execute(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            requester_protheus_user_ids=requester_protheus_user_id,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            result,
            operation_id="list_supplies_purchase_request_lines",
            message="Linhas de solicitações de compra carregadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar linhas de SC: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao listar linhas de SC: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para as solicitações de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao listar linhas de solicitações de compra: {exc}")
        return error_response(
            "Erro interno ao listar linhas de solicitações de compra.",
            status_code=500,
        )


@router.get("/requesters")
@require_any_permission(PURCHASE_REQUESTS_READ_PERMISSIONS)
def list_supplies_purchase_request_requesters_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    cost_centers: Annotated[list[str] | None, Query()] = None,
    request_number: str | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    order_number: str | None = Query(None),
):
    branch_error = purchase_requests_branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_supplies_purchase_request_requesters_use_case()
        result = use_case.execute(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
        )
        return api_delpi_success(
            result,
            operation_id="list_supplies_purchase_request_requesters",
            message="Solicitantes de compra carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar solicitantes de SC: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao listar solicitantes de SC: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para os solicitantes de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao listar solicitantes de SC: {exc}")
        return error_response(
            "Erro interno ao listar solicitantes de compra.",
            status_code=500,
        )


@router.get(
    "/lines/{branch}/{request_number}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_purchase_request_lines",
        path="/supplies/purchase-requests/lines/{branch}/{request_number}",
    ),
)
@require_any_permission(PURCHASE_REQUESTS_READ_PERMISSIONS)
def get_supplies_purchase_request_lines_route(
    branch: str,
    request_number: str,
    date_from: str | None = Query(None, alias="date_from"),
    date_to: str | None = Query(None, alias="date_to"),
    cost_centers: Annotated[list[str] | None, Query()] = None,
):
    branch_error = purchase_requests_branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_supplies_purchase_request_lines_use_case()
        result = use_case.execute(
            branch=branch,
            request_number=request_number,
            cost_centers=cost_centers,
            date_from=date_from,
            date_to=date_to,
        )
        return api_delpi_success(
            result,
            operation_id="get_supplies_purchase_request_lines",
            message="Detalhe TOTVS da solicitação de compra carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao obter linhas de SC: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao obter linhas de SC: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para a solicitação de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao obter linhas da solicitação de compra: {exc}")
        return error_response(
            "Erro interno ao obter linhas da solicitação de compra.",
            status_code=500,
        )


@router.get(
    "/recent-linked-orders",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_purchase_request_recent_linked_orders",
        path="/supplies/purchase-requests/recent-linked-orders",
    ),
)
@require_auth()
def list_supplies_purchase_request_recent_linked_orders_route(
    after_recno: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    try:
        use_case = build_list_supplies_purchase_request_recent_linked_orders_use_case()
        result = use_case.execute(after_recno=after_recno, limit=limit)
        return api_delpi_success(
            result,
            operation_id="list_supplies_purchase_request_recent_linked_orders",
            message="Pedidos de compra recém-vinculados à SC carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar PCs vinculados à SC: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao listar PCs vinculados à SC: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para os pedidos vinculados à SC.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao listar PCs vinculados à SC: {exc}")
        return error_response(
            "Erro interno ao listar pedidos de compra vinculados à SC.",
            status_code=500,
        )

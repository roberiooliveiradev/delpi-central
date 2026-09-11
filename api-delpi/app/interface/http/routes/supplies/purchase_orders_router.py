"""Rotas — worklist de pedidos de compra em aberto (SC7)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import build_list_supplies_purchase_orders_use_case
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.query_param_enums import BRANCH_QUERY_REQUIRED
from app.interface.http.routes.supplies.purchase_orders_branch_access import (
    branch_access_error,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/purchase-orders",
    tags=["Suprimentos — Pedidos de compra"],
)


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_purchase_orders",
        path="/supplies/purchase-orders",
    ),
)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def list_supplies_purchase_orders_route(
    branch: str = BRANCH_QUERY_REQUIRED(),
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
    order_number: str | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    expected_delivery_from: str | None = Query(None),
    expected_delivery_to: str | None = Query(None),
    late_only: bool = Query(False),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_supplies_purchase_orders_use_case()
        result = use_case.execute(
            branch=branch,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            result,
            operation_id="list_supplies_purchase_orders",
            message="Pedidos de compra em aberto carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar pedidos de compra em aberto: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao listar pedidos de compra em aberto: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para os pedidos de compra em aberto.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao listar pedidos de compra em aberto: {exc}")
        return error_response(
            "Erro interno ao listar pedidos de compra em aberto.",
            status_code=500,
        )

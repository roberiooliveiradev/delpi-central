"""Rotas — worklist de pedidos de compra em aberto (SC7)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.interface.http.supplies_bff_service_access import (
    require_any_permission_or_supplies_bff,
)

from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import (
    build_get_supplies_purchase_order_use_case,
    build_list_supplies_purchase_orders_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.query_param_enums import (
    BRANCH_CODES_QUERY,
    BRANCH_PATH,
    ORDER_NUMBER_PATH,
    SORT_DIR_QUERY_OPTIONAL,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    PURCHASE_ORDERS_SORT_FIELDS,
    normalize_purchase_order_branches,
)
from app.interface.http.routes.supplies.purchase_orders_branch_access import (
    branches_access_error,
    branch_access_error,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/purchase-orders",
    tags=["Suprimentos — Pedidos de compra"],
)


def _list_kwargs(
    *,
    branch: list[str],
    order_number: str | None,
    product_code: str | None,
    supplier_code: str | None,
    expected_delivery_from: str | None,
    expected_delivery_to: str | None,
    late_only: bool,
    sort_by: str | None,
    sort_dir: str | None,
) -> dict:
    branches = normalize_purchase_order_branches(branches=branch)
    return {
        "branches": branches,
        "order_number": order_number,
        "product_code": product_code,
        "supplier_code": supplier_code,
        "expected_delivery_from": expected_delivery_from,
        "expected_delivery_to": expected_delivery_to,
        "late_only": late_only,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_purchase_orders",
        path="/supplies/purchase-orders",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def list_supplies_purchase_orders_route(
    branch: list[str] = BRANCH_CODES_QUERY(),
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
    order_number: str | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    expected_delivery_from: str | None = Query(None),
    expected_delivery_to: str | None = Query(None),
    late_only: bool = Query(False),
    sort_by: str | None = Query(
        None,
        description="Allow-listed sort field for open purchase order lines.",
        enum=list(PURCHASE_ORDERS_SORT_FIELDS),
    ),
    sort_dir: str | None = SORT_DIR_QUERY_OPTIONAL(),
):
    try:
        kwargs = _list_kwargs(
            branch=branch,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=422)

    branch_error = branches_access_error(kwargs["branches"])
    if branch_error:
        return branch_error

    try:
        use_case = build_list_supplies_purchase_orders_use_case()
        result = use_case.execute(
            page=page,
            page_size=page_size,
            **kwargs,
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


@router.get(
    "/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_supplies_purchase_orders",
        path="/supplies/purchase-orders/export",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def export_supplies_purchase_orders_route(
    branch: list[str] = BRANCH_CODES_QUERY(),
    order_number: str | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    expected_delivery_from: str | None = Query(None),
    expected_delivery_to: str | None = Query(None),
    late_only: bool = Query(False),
    sort_by: str | None = Query(
        None,
        description="Allow-listed sort field for the export dataset.",
        enum=list(PURCHASE_ORDERS_SORT_FIELDS),
    ),
    sort_dir: str | None = SORT_DIR_QUERY_OPTIONAL(),
):
    try:
        kwargs = _list_kwargs(
            branch=branch,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=422)

    branch_error = branches_access_error(kwargs["branches"])
    if branch_error:
        return branch_error

    try:
        use_case = build_list_supplies_purchase_orders_use_case()
        result = use_case.export(**kwargs)
        return api_delpi_success(
            result,
            operation_id="export_supplies_purchase_orders",
            message="Dataset de pedidos de compra em aberto exportado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao exportar pedidos de compra em aberto: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao exportar pedidos de compra em aberto: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para exportar os pedidos de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao exportar pedidos de compra em aberto: {exc}")
        return error_response(
            "Erro interno ao exportar pedidos de compra em aberto.",
            status_code=500,
        )


@router.get(
    "/{branch}/{order_number}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_purchase_order",
        path="/supplies/purchase-orders/{branch}/{order_number}",
    ),
)
@require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)
def get_supplies_purchase_order(
    branch: str = BRANCH_PATH(),
    order_number: str = ORDER_NUMBER_PATH(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_supplies_purchase_order_use_case()
        result = use_case.execute(branch=branch, order_number=order_number)
        if result is None:
            return not_found_response("Pedido de compra não encontrado.")
        return api_delpi_success(
            result,
            operation_id="get_supplies_purchase_order",
            message="Pedido de compra em aberto carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar pedido de compra: {exc}")
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao carregar pedido de compra: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para o pedido de compra.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao carregar pedido de compra: {exc}")
        return error_response(
            "Erro interno ao carregar o pedido de compra.",
            status_code=500,
        )

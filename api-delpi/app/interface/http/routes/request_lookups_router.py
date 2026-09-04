"""HTTP lookups canônicos para Request Engine (E17) — sem prefixo /invoice-issuance."""

from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import REQUEST_LOOKUPS_PERMISSIONS
from app.composition.invoice_issuance_composer import (
    build_open_sales_orders_use_case,
    build_search_carriers_use_case,
    build_search_parties_use_case,
    build_search_products_use_case,
    build_warehouse_balance_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.invoice_issuance.exceptions import InvoiceIssuanceError
from app.interface.http.pagination_query import LIMIT_QUERY
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    INVOICE_ISSUANCE_PARTY_TYPE_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.invoice_issuance.invoice_issuance_branch_access import (
    branch_access_error,
)
from app.utils.logger import log_error

router = APIRouter(prefix="/request-lookups", tags=["Request lookups"])


def _gate_branch(branch_raw: str | None):
    branch = str(branch_raw or "").strip()
    if branch not in {"01", "02"}:
        return error_response(
            "Filial inválida. Use 01 ou 02.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    return branch_access_error(branch)


def _handle_domain(exc: InvoiceIssuanceError):
    meta = getattr(exc, "meta", None) or None
    if exc.status_code == 404:
        return not_found_response(str(exc), code=exc.code)
    return error_response(
        str(exc),
        status_code=exc.status_code,
        code=exc.code,
        recoverable=exc.status_code in {400, 409, 422},
        meta=meta,
    )


@router.get("/parties", operation_id="search_request_lookup_parties")
@require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)
def search_parties(
    party_type: str = INVOICE_ISSUANCE_PARTY_TYPE_QUERY(),
    query: str = Query(..., min_length=2),
    limit: int = LIMIT_QUERY("limit_20_50"),
):
    try:
        items = build_search_parties_use_case().execute(
            party_type=party_type, query=query, limit=limit
        )
        return api_delpi_success(
            {"items": items}, operation_id="search_request_lookup_parties"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_request_lookup_parties failed: {exc}")
        return error_response("Falha ao buscar destinatário.", status_code=500)


@router.get("/products", operation_id="search_request_lookup_products")
@require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)
def search_products(
    query: str = Query(..., min_length=2),
    limit: int = LIMIT_QUERY("limit_20_50"),
):
    try:
        items = build_search_products_use_case().execute(query=query, limit=limit)
        return api_delpi_success(
            {"items": items}, operation_id="search_request_lookup_products"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_request_lookup_products failed: {exc}")
        return error_response("Falha ao buscar itens.", status_code=500)


@router.get("/carriers", operation_id="search_request_lookup_carriers")
@require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)
def search_carriers(
    query: str = Query(..., min_length=2),
    limit: int = LIMIT_QUERY("limit_20_50"),
):
    try:
        items = build_search_carriers_use_case().execute(query=query, limit=limit)
        return api_delpi_success(
            {"items": items}, operation_id="search_request_lookup_carriers"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_request_lookup_carriers failed: {exc}")
        return error_response("Falha ao buscar transportadora.", status_code=500)


@router.get(
    "/products/{code}/warehouse-01-balance",
    operation_id="get_request_lookup_warehouse_01_balance",
)
@require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)
def warehouse_balance(code: str, branch: str = BRANCH_QUERY_REQUIRED()):
    denied = _gate_branch(branch)
    if denied is not None:
        return denied
    try:
        data = build_warehouse_balance_use_case().execute(
            product_code=code, branch_code=branch
        )
        return api_delpi_success(
            data, operation_id="get_request_lookup_warehouse_01_balance"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"get_request_lookup_warehouse_01_balance failed: {exc}")
        return error_response("Falha ao consultar saldo.", status_code=500)


@router.get(
    "/open-sales-orders",
    operation_id="list_request_lookup_open_sales_orders",
)
@require_any_permission(REQUEST_LOOKUPS_PERMISSIONS)
def list_open_sales_orders(
    branch: str = BRANCH_QUERY_REQUIRED(),
    party_code: str = Query(..., min_length=1),
    party_store: str = Query(..., min_length=1),
):
    denied = _gate_branch(branch)
    if denied is not None:
        return denied
    try:
        data = build_open_sales_orders_use_case().execute(
            branch_code=branch,
            party_code=party_code,
            party_store=party_store,
        )
        return api_delpi_success(
            data, operation_id="list_request_lookup_open_sales_orders"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"list_request_lookup_open_sales_orders failed: {exc}")
        return error_response("Falha ao listar pedidos em aberto.", status_code=500)

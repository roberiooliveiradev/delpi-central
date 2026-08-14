"""HTTP routes — invoice-issuance."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    INVOICE_ISSUANCE_ACCESS,
    INVOICE_ISSUANCE_CREATE,
    INVOICE_ISSUANCE_CREATE_PERMISSIONS,
    INVOICE_ISSUANCE_MANAGE,
    INVOICE_ISSUANCE_PROCESS,
    INVOICE_ISSUANCE_PROCESS_PERMISSIONS,
    INVOICE_ISSUANCE_READ_PERMISSIONS,
    INVOICE_ISSUANCE_VIEW,
)
from app.application.use_cases.invoice_issuance.invoice_issuance_use_cases import Actor
from app.composition.invoice_issuance_composer import (
    build_cancel_use_case,
    build_create_use_case,
    build_get_use_case,
    build_issue_use_case,
    build_list_use_case,
    build_open_sales_orders_use_case,
    build_resubmit_use_case,
    build_return_use_case,
    build_search_carriers_use_case,
    build_search_parties_use_case,
    build_search_products_use_case,
    build_start_use_case,
    build_update_returned_use_case,
    build_warehouse_balance_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.domain.services.invoice_issuance.exceptions import InvoiceIssuanceError
from app.interface.http.routes.invoice_issuance.invoice_issuance_branch_access import (
    branch_access_error,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    INVOICE_ISSUANCE_INVOICE_TYPE_QUERY_OPTIONAL,
    INVOICE_ISSUANCE_PARTY_TYPE_QUERY,
    INVOICE_ISSUANCE_STATUS_QUERY_OPTIONAL,
)
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(
    prefix="/invoice-issuance",
    tags=["Invoice issuance"],
)


class ItemBody(BaseModel):
    product_code: str
    product_description: str = ""
    quantity: float | str
    unit_price: float | str
    stock_write_off: bool | None = None
    sales_order: str | None = None
    sales_order_item: str | None = None
    customer_order_number: str | None = None


class ChecklistBody(BaseModel):
    recipient: bool = False
    item_codes: bool = False
    quantity_price: bool = False
    stock_write_off: bool = False
    invoice_type: bool = False
    freight_mode: bool = False
    weight_volumes: bool = False


class CreateRequestBody(BaseModel):
    branch_code: str = Field(..., alias="branch")
    party_type: str
    party_code: str
    party_store: str
    invoice_type: str
    invoice_type_other: str | None = None
    freight_mode: str
    carrier_code: str | None = None
    carrier_name: str | None = None
    weight_kg: float | str
    volume_count: int
    observation: str | None = None
    checklist: ChecklistBody | None = None
    items: list[ItemBody]

    model_config = {"populate_by_name": True}


class ReturnBody(BaseModel):
    reason: str


class CancelBody(BaseModel):
    justification: str


def _actor() -> Actor:
    user = get_current_user()
    if user is None:
        return Actor(user_id="unknown", user_name="Usuário")
    user_id = str(getattr(user, "id", "") or "unknown")
    raw_name = getattr(user, "name", None) or getattr(user, "email", None) or "Usuário"
    return Actor(
        user_id=user_id,
        user_name=format_person_name(str(raw_name)),
        has_access=bool(has_permission(user, INVOICE_ISSUANCE_ACCESS)),
        has_create=bool(has_permission(user, INVOICE_ISSUANCE_CREATE)),
        has_view=bool(has_permission(user, INVOICE_ISSUANCE_VIEW)),
        has_process=bool(has_permission(user, INVOICE_ISSUANCE_PROCESS)),
        has_manage=bool(has_permission(user, INVOICE_ISSUANCE_MANAGE)),
    )


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


def _gate_loaded(data: dict[str, Any]):
    payload = data.get("request") if isinstance(data.get("request"), dict) else data
    branch = str((payload or {}).get("branch_code") or "").strip()
    if not branch:
        return error_response(
            "Solicitação sem filial.",
            status_code=500,
            code="INTERNAL_ERROR",
            recoverable=False,
        )
    return branch_access_error(branch)


@router.get("/parties", operation_id="search_invoice_issuance_parties")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def search_parties(
    party_type: str = INVOICE_ISSUANCE_PARTY_TYPE_QUERY(),
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
):
    try:
        items = build_search_parties_use_case().execute(
            party_type=party_type, query=query, limit=limit
        )
        return api_delpi_success({"items": items}, operation_id="search_invoice_issuance_parties")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_invoice_issuance_parties failed: {exc}")
        return error_response("Falha ao buscar destinatário.", status_code=500)


@router.get("/products", operation_id="search_invoice_issuance_products")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def search_products(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
):
    try:
        items = build_search_products_use_case().execute(query=query, limit=limit)
        return api_delpi_success({"items": items}, operation_id="search_invoice_issuance_products")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_invoice_issuance_products failed: {exc}")
        return error_response("Falha ao buscar itens.", status_code=500)


@router.get("/carriers", operation_id="search_invoice_issuance_carriers")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def search_carriers(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
):
    try:
        items = build_search_carriers_use_case().execute(query=query, limit=limit)
        return api_delpi_success(
            {"items": items}, operation_id="search_invoice_issuance_carriers"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"search_invoice_issuance_carriers failed: {exc}")
        return error_response("Falha ao buscar transportadora.", status_code=500)


@router.get(
    "/products/{code}/warehouse-01-balance",
    operation_id="get_invoice_issuance_warehouse_01_balance",
)
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def warehouse_balance(code: str, branch: str = BRANCH_QUERY_REQUIRED()):
    denied = _gate_branch(branch)
    if denied is not None:
        return denied
    try:
        data = build_warehouse_balance_use_case().execute(
            product_code=code, branch_code=branch
        )
        return api_delpi_success(data, operation_id="get_invoice_issuance_warehouse_01_balance")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"get_invoice_issuance_warehouse_01_balance failed: {exc}")
        return error_response("Falha ao consultar saldo.", status_code=500)


@router.get(
    "/open-sales-orders",
    operation_id="list_invoice_issuance_open_sales_orders",
)
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
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
            data, operation_id="list_invoice_issuance_open_sales_orders"
        )
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"list_invoice_issuance_open_sales_orders failed: {exc}")
        return error_response("Falha ao consultar pedidos de venda em aberto.", status_code=500)


@router.post("/requests", operation_id="create_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def create_request(body: CreateRequestBody):
    denied = _gate_branch(body.branch_code)
    if denied is not None:
        return denied
    try:
        data = build_create_use_case().execute(body.model_dump(by_alias=False), _actor())
        return api_delpi_success(data, operation_id="create_invoice_issuance_request")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"create_invoice_issuance_request failed: {exc}")
        return error_response("Falha ao criar solicitação.", status_code=500)


@router.get("/requests", operation_id="list_invoice_issuance_requests")
@require_any_permission(INVOICE_ISSUANCE_READ_PERMISSIONS)
def list_requests(
    branch: str = BRANCH_QUERY_REQUIRED(),
    status: str | None = INVOICE_ISSUANCE_STATUS_QUERY_OPTIONAL(),
    invoice_type: str | None = INVOICE_ISSUANCE_INVOICE_TYPE_QUERY_OPTIONAL(),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    denied = _gate_branch(branch)
    if denied is not None:
        return denied
    try:
        data = build_list_use_case().execute(
            actor=_actor(),
            filters={
                "branch": branch,
                "status": status,
                "invoice_type": invoice_type,
                "q": q,
            },
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(data, operation_id="list_invoice_issuance_requests")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"list_invoice_issuance_requests failed: {exc}")
        return error_response("Falha ao listar solicitações.", status_code=500)


@router.get("/requests/{request_id}", operation_id="get_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_READ_PERMISSIONS)
def get_request(request_id: UUID):
    try:
        data = build_get_use_case().execute(str(request_id), _actor())
        denied = _gate_loaded(data)
        if denied is not None:
            return denied
        return api_delpi_success(data, operation_id="get_invoice_issuance_request")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"get_invoice_issuance_request failed: {exc}")
        return error_response("Falha ao carregar solicitação.", status_code=500)


@router.patch("/requests/{request_id}", operation_id="update_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def update_request(request_id: UUID, body: CreateRequestBody):
    denied = _gate_branch(body.branch_code)
    if denied is not None:
        return denied
    try:
        data = build_update_returned_use_case().execute(
            str(request_id), body.model_dump(by_alias=False), _actor()
        )
        return api_delpi_success(data, operation_id="update_invoice_issuance_request")
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"update_invoice_issuance_request failed: {exc}")
        return error_response("Falha ao atualizar solicitação.", status_code=500)


def _action_route(request_id: UUID, builder, operation_id: str, **kwargs):
    try:
        data = builder().execute(str(request_id), _actor(), **kwargs)
        denied = _gate_loaded(data)
        if denied is not None:
            return denied
        return api_delpi_success(data, operation_id=operation_id)
    except InvoiceIssuanceError as exc:
        return _handle_domain(exc)
    except Exception as exc:
        log_error(f"{operation_id} failed: {exc}")
        return error_response("Falha ao atualizar solicitação.", status_code=500)


@router.post("/requests/{request_id}/resubmit", operation_id="resubmit_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def resubmit_request(request_id: UUID):
    return _action_route(request_id, build_resubmit_use_case, "resubmit_invoice_issuance_request")


@router.post("/requests/{request_id}/start", operation_id="start_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_PROCESS_PERMISSIONS)
def start_request(request_id: UUID):
    return _action_route(request_id, build_start_use_case, "start_invoice_issuance_request")


@router.post("/requests/{request_id}/return", operation_id="return_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_PROCESS_PERMISSIONS)
def return_request(request_id: UUID, body: ReturnBody):
    return _action_route(
        request_id,
        build_return_use_case,
        "return_invoice_issuance_request",
        reason=body.reason,
    )


@router.post("/requests/{request_id}/issue", operation_id="issue_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_PROCESS_PERMISSIONS)
def issue_request(request_id: UUID):
    return _action_route(request_id, build_issue_use_case, "issue_invoice_issuance_request")


@router.post("/requests/{request_id}/cancel", operation_id="cancel_invoice_issuance_request")
@require_any_permission(INVOICE_ISSUANCE_CREATE_PERMISSIONS)
def cancel_request(request_id: UUID, body: CancelBody):
    return _action_route(
        request_id,
        build_cancel_use_case,
        "cancel_invoice_issuance_request",
        justification=body.justification,
    )

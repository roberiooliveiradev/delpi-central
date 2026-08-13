from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, File, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_manage_portfolios,
    can_use_team_scope,
)
from commercial_app.application.use_cases.manage_account_contacts import (
    CreateAccountContactInput,
)
from commercial_app.application.use_cases.manage_seller_portfolio import parse_customer_assignments
from commercial_app.composition.commercial_composer import (
    build_delpi_commercial_gateway,
    build_manage_account_contacts_use_case,
    build_manage_customer_avatar_use_case,
    build_resolve_commercial_customer_scope_service,
)
from commercial_app.core.auth_actor import (
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.schemas.account_contact_schemas import (
    CreateAccountContactBody,
    UpdateAccountContactBody,
)
from commercial_app.interface.http.schemas.portfolio_schemas import (
    BillingSeriesBody,
    EnrichmentBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


def _customer_scope_for_request(request: Request):
    user = current_user_from_request(request)
    unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
    user_id = actor_sub_from_request(request) or ""
    return build_resolve_commercial_customer_scope_service().execute(
        user_id=user_id,
        unrestricted=unrestricted,
    )


def _account_detail_scope_check(_request: Request):
    """
    Conta (par único): `accounts.view` basta — sem membership.
    Listas/KPIs continuam com filter_pairs no escopo de carteira.
    """

    def check(_customer_code: str, _customer_store: str) -> None:
        return None

    return check


def _pairs_for_account_or_portfolio_list(
    scope,
    pairs: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """
    Um par = detalhe Conta (sem filtro membership).
    Vários pares = lista/KPI/multi-select (KEEP filtro de carteira).
    Deduplica preservando ordem após normalização/filtro.
    """
    normalized = [
        (str(code or "").strip(), str(store or "").strip())
        for code, store in pairs
        if str(code or "").strip() and str(store or "").strip()
    ]
    if len(normalized) <= 1:
        return normalized
    filtered = build_resolve_commercial_customer_scope_service().filter_pairs(
        scope,
        normalized,
    )
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for pair in filtered:
        if pair in seen:
            continue
        seen.add(pair)
        unique.append(pair)
    return unique


@router.get("/search", operation_id="search_active_customers_for_portfolio")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def search_active_customers(
    _request: Request,
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        payload = build_delpi_commercial_gateway().search_active_customers(
            params={"q": q, "page": page, "page_size": page_size},
        )
        return ok(payload.get("data", payload), message="Clientes encontrados.")
    except RuntimeError as exc:
        return fail(str(exc), 502)
    except Exception:
        logger.exception("search_active_customers_failed")
        return fail("Erro interno ao buscar clientes.", 500)


@router.post("/enrichment", operation_id="enrich_portfolio_customers")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def enrich_portfolio_customers(request: Request, body: EnrichmentBody = Body(...)):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        scope = _customer_scope_for_request(request)
        allowed_pairs = _pairs_for_account_or_portfolio_list(
            scope,
            [(item.customer_code, item.customer_store) for item in customers],
        )
        payload: dict[str, Any] = {
            "customers": [
                {
                    "customer_code": code,
                    "customer_store": store,
                }
                for code, store in allowed_pairs
            ]
        }
        result = build_delpi_commercial_gateway().enrich_portfolio_customers(payload=payload)
        data = result.get("data", result)
        # api-delpi marca has_avatar pelo schema/arquivo legado PVA; o MFE baixa
        # avatar via commercial-api — alinhar flag ao storage canônico.
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list) and items:
            avatar_keys = build_manage_customer_avatar_use_case().list_keys_with_avatar(
                customers=[
                    (
                        str(item.get("customer_code") or "").strip(),
                        str(item.get("customer_store") or "").strip(),
                    )
                    for item in items
                    if isinstance(item, dict)
                ]
            )
            for item in items:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("customer_code") or "").strip()
                store = str(item.get("customer_store") or "").strip()
                has_avatar = bool(code and store and (code, store) in avatar_keys)
                item["has_avatar"] = has_avatar
                item["avatar_url"] = (
                    f"/customers/{code}/{store}/avatar" if has_avatar else None
                )
        return ok(data, message="Clientes enriquecidos.")
    except ValueError as exc:
        return fail(str(exc), 400)
    except RuntimeError as exc:
        return fail(str(exc), 502)
    except Exception:
        logger.exception("enrich_portfolio_customers_failed")
        return fail("Erro interno ao enriquecer clientes.", 500)


@router.post("/billing-series", operation_id="list_commercial_customer_billing_series")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_customer_billing_series(
    request: Request,
    body: BillingSeriesBody = Body(...),
):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        scope = _customer_scope_for_request(request)
        allowed_pairs = _pairs_for_account_or_portfolio_list(
            scope,
            [(item.customer_code, item.customer_store) for item in customers],
        )
        if not allowed_pairs:
            return ok(
                {
                    "months": body.months,
                    "customer_count": 0,
                    "points": [],
                    **(
                        {"start_date": body.start_date, "end_date": body.end_date}
                        if body.start_date and body.end_date
                        else {}
                    ),
                    **({"granularity": body.granularity} if body.granularity else {}),
                },
                message="Faturamento mensal carregado.",
                operation_id="list_commercial_customer_billing_series",
            )
        payload: dict[str, Any] = {
            "customers": [
                {"customer_code": code, "customer_store": store}
                for code, store in allowed_pairs
            ],
            "months": body.months,
        }
        if body.start_date and body.end_date:
            payload["start_date"] = body.start_date
            payload["end_date"] = body.end_date
        if body.granularity:
            payload["granularity"] = body.granularity
        result = build_delpi_commercial_gateway().list_customer_billing_series(
            payload=payload
        )
        data = result.get("data", result)
        return ok(
            data,
            message="Faturamento mensal carregado.",
            operation_id="list_commercial_customer_billing_series",
        )
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_commercial_customer_billing_series")
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="list_commercial_customer_billing_series")
    except Exception:
        logger.exception("list_commercial_customer_billing_series_failed")
        return fail(
            "Erro interno ao carregar faturamento mensal.",
            500,
            operation_id="list_commercial_customer_billing_series",
        )


@router.get(
    "/{customer_code}/{customer_store}/outbound-invoices",
    operation_id="list_commercial_customer_outbound_invoices",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_customer_outbound_invoices(
    _request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    situation: str | None = Query(default="all"),
    search: str | None = Query(default=None),
):
    try:
        result = build_delpi_commercial_gateway().list_customer_outbound_invoices(
            customer_code=customer_code,
            customer_store=customer_store,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": page_size,
                "situation": situation,
                "search": search,
            },
        )
        data = result.get("data", result)
        return ok(
            data,
            message="Notas fiscais do cliente carregadas.",
            operation_id="list_commercial_customer_outbound_invoices",
        )
    except LookupError as exc:
        return fail(
            str(exc),
            404,
            operation_id="list_commercial_customer_outbound_invoices",
        )
    except RuntimeError as exc:
        return fail(
            str(exc),
            502,
            operation_id="list_commercial_customer_outbound_invoices",
        )
    except Exception:
        logger.exception("list_commercial_customer_outbound_invoices_failed")
        return fail(
            "Erro interno ao carregar notas fiscais do cliente.",
            500,
            operation_id="list_commercial_customer_outbound_invoices",
        )


@router.get(
    "/{customer_code}/{customer_store}/outbound-invoices/{branch}/{invoice_number}/{invoice_series}",
    operation_id="get_commercial_customer_outbound_invoice",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def get_commercial_customer_outbound_invoice(
    _request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    branch: str = Path(..., min_length=1),
    invoice_number: str = Path(..., min_length=1),
    invoice_series: str = Path(..., min_length=1),
):
    """Detalhe de NF de saída (SF2/SD2) no contexto da Conta — proxy TOTVS via api-delpi."""
    try:
        result = build_delpi_commercial_gateway().get_outbound_invoice(
            branch=branch,
            invoice_number=invoice_number,
            invoice_series=invoice_series,
        )
        data = result.get("data", result)
        if not isinstance(data, dict):
            return fail(
                "Nota fiscal de saída não encontrada.",
                404,
                operation_id="get_commercial_customer_outbound_invoice",
            )
        invoice_customer = str(data.get("customer_code") or "").strip()
        invoice_store = str(data.get("customer_store") or "").strip()
        if invoice_customer and invoice_customer != str(customer_code).strip():
            return fail(
                "Nota fiscal de saída não encontrada para este cliente.",
                404,
                operation_id="get_commercial_customer_outbound_invoice",
            )
        if invoice_store and invoice_store != str(customer_store).strip():
            return fail(
                "Nota fiscal de saída não encontrada para este cliente.",
                404,
                operation_id="get_commercial_customer_outbound_invoice",
            )
        return ok(
            data,
            message="Nota fiscal do cliente carregada.",
            operation_id="get_commercial_customer_outbound_invoice",
        )
    except LookupError as exc:
        return fail(
            str(exc),
            404,
            operation_id="get_commercial_customer_outbound_invoice",
        )
    except RuntimeError as exc:
        return fail(
            str(exc),
            502,
            operation_id="get_commercial_customer_outbound_invoice",
        )
    except Exception:
        logger.exception("get_commercial_customer_outbound_invoice_failed")
        return fail(
            "Erro interno ao carregar a nota fiscal do cliente.",
            500,
            operation_id="get_commercial_customer_outbound_invoice",
        )


@router.get(
    "/{customer_code}/{customer_store}/open-orders",
    operation_id="list_commercial_customer_open_orders",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_customer_open_orders(
    _request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    """Conta 360: pedidos do par código/loja sem filtro de membership."""
    try:
        result = build_delpi_commercial_gateway().list_open_orders_by_customer(
            customer_code=customer_code,
            customer_store=customer_store,
        )
        data = result.get("data", result)
        return ok(
            data,
            message="Pedidos em aberto do cliente carregados.",
            operation_id="list_commercial_customer_open_orders",
        )
    except LookupError as exc:
        return fail(
            str(exc),
            404,
            operation_id="list_commercial_customer_open_orders",
        )
    except RuntimeError as exc:
        return fail(
            str(exc),
            502,
            operation_id="list_commercial_customer_open_orders",
        )
    except Exception:
        logger.exception("list_commercial_customer_open_orders_failed")
        return fail(
            "Erro interno ao carregar pedidos em aberto do cliente.",
            500,
            operation_id="list_commercial_customer_open_orders",
        )


@router.get(
    "/{customer_code}/{customer_store}/contacts-bundle",
    operation_id="get_customer_contacts_bundle",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def get_customer_contacts_bundle(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        items = build_manage_account_contacts_use_case().list(
            customer_code=customer_code,
            customer_store=customer_store,
            scope_check=_account_detail_scope_check(request),
        )
        totvs_contact = None
        try:
            totvs_contact = build_delpi_commercial_gateway().fetch_totvs_customer_contact(
                customer_code=customer_code,
                customer_store=customer_store,
            )
        except Exception:
            logger.exception("fetch_totvs_customer_contact_failed")
        return ok(
            {
                "totvs_contact": totvs_contact,
                "items": [item.to_dict() for item in items],
            },
            message="Contatos carregados.",
            operation_id="get_customer_contacts_bundle",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="get_customer_contacts_bundle")
    except Exception:
        logger.exception("get_customer_contacts_bundle_failed")
        return fail(
            "Erro interno ao carregar contatos.",
            500,
            operation_id="get_customer_contacts_bundle",
        )


@router.get(
    "/{customer_code}/{customer_store}/audit",
    operation_id="list_customer_account_audit",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def list_customer_account_audit(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    page: int = Query(1, ge=1, description="Página (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página."),
):
    """Timeline de audit_log da Conta (contatos e avatar)."""
    try:
        payload = build_manage_account_contacts_use_case().list_account_audit(
            customer_code=customer_code,
            customer_store=customer_store,
            scope_check=_account_detail_scope_check(request),
            page=page,
            page_size=page_size,
        )
        return ok(
            payload,
            message="Auditoria da conta carregada.",
            operation_id="list_customer_account_audit",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="list_customer_account_audit")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_customer_account_audit")
    except Exception:
        logger.exception("list_customer_account_audit_failed")
        return fail(
            "Erro interno ao listar auditoria da conta.",
            500,
            operation_id="list_customer_account_audit",
        )


@router.post(
    "/{customer_code}/{customer_store}/contacts",
    operation_id="create_customer_contact",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def create_customer_contact(
    request: Request,
    body: CreateAccountContactBody,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        contact = build_manage_account_contacts_use_case().create(
            customer_code=customer_code,
            customer_store=customer_store,
            actor_user_id=actor_sub_from_request(request) or "",
            data=CreateAccountContactInput(
                full_name=body.full_name,
                role_title=body.role_title,
                channel=body.channel,
                email=body.email,
                phone_e164=body.phone_e164,
                is_whatsapp=body.is_whatsapp,
                is_primary=body.is_primary,
                source=body.source,
            ),
            scope_check=_account_detail_scope_check(request),
        )
        return ok(
            contact.to_dict(),
            message="Contato criado.",
            operation_id="create_customer_contact",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="create_customer_contact")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="create_customer_contact")
    except Exception:
        logger.exception("create_customer_contact_failed")
        return fail(
            "Erro interno ao criar contato.",
            500,
            operation_id="create_customer_contact",
        )


@router.patch(
    "/{customer_code}/{customer_store}/contacts/{contact_id}",
    operation_id="update_customer_contact",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def update_customer_contact(
    request: Request,
    body: UpdateAccountContactBody,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    contact_id: UUID = Path(...),
):
    try:
        contact = build_manage_account_contacts_use_case().update(
            customer_code=customer_code,
            customer_store=customer_store,
            contact_id=contact_id,
            changes=body.model_dump(exclude_unset=True),
            scope_check=_account_detail_scope_check(request),
            actor_user_id=actor_sub_from_request(request) or "",
        )
        return ok(
            contact.to_dict(),
            message="Contato atualizado.",
            operation_id="update_customer_contact",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="update_customer_contact")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="update_customer_contact")
    except Exception:
        logger.exception("update_customer_contact_failed")
        return fail(
            "Erro interno ao atualizar contato.",
            500,
            operation_id="update_customer_contact",
        )


@router.delete(
    "/{customer_code}/{customer_store}/contacts/{contact_id}",
    operation_id="delete_customer_contact",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def delete_customer_contact(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    contact_id: UUID = Path(...),
):
    try:
        contact = build_manage_account_contacts_use_case().soft_delete(
            customer_code=customer_code,
            customer_store=customer_store,
            contact_id=contact_id,
            scope_check=_account_detail_scope_check(request),
            actor_user_id=actor_sub_from_request(request) or "",
        )
        return ok(
            {"deleted": True, "id": str(contact.id)},
            message="Contato removido.",
            operation_id="delete_customer_contact",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="delete_customer_contact")
    except Exception:
        logger.exception("delete_customer_contact_failed")
        return fail(
            "Erro interno ao remover contato.",
            500,
            operation_id="delete_customer_contact",
        )


@router.get(
    "/{customer_code}/{customer_store}/avatar",
    operation_id="get_customer_avatar",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_customer_avatar(
    _request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        avatar_file = build_manage_customer_avatar_use_case().get_file(
            customer_code=customer_code,
            customer_store=customer_store,
        )
        return FileResponse(
            path=avatar_file.path,
            media_type=avatar_file.content_type,
            filename=avatar_file.file_name,
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="get_customer_avatar")
    except Exception:
        logger.exception("get_customer_avatar_failed")
        return fail(
            "Erro interno ao carregar avatar.",
            500,
            operation_id="get_customer_avatar",
        )


@router.put(
    "/{customer_code}/{customer_store}/avatar",
    operation_id="upsert_customer_avatar",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
async def upsert_customer_avatar(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        record = build_manage_customer_avatar_use_case().upsert(
            customer_code=customer_code,
            customer_store=customer_store,
            original_name=file.filename or "avatar.bin",
            content=content,
            mime_type=file.content_type,
            uploaded_by_user_id=actor_sub_from_request(request),
        )
        return ok(
            {
                "customer_code": record.customer_code,
                "customer_store": record.customer_store,
                "file_name": record.file_name,
                "content_type": record.content_type,
                "storage_key": record.storage_key,
                "byte_size": record.byte_size,
            },
            message="Avatar atualizado com sucesso.",
            operation_id="upsert_customer_avatar",
        )
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="upsert_customer_avatar")
    except Exception:
        logger.exception("upsert_customer_avatar_failed")
        return fail(
            "Erro interno ao gravar avatar.",
            500,
            operation_id="upsert_customer_avatar",
        )


@router.delete(
    "/{customer_code}/{customer_store}/avatar",
    operation_id="delete_customer_avatar",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def delete_customer_avatar(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        build_manage_customer_avatar_use_case().delete(
            customer_code=customer_code,
            customer_store=customer_store,
            actor_user_id=actor_sub_from_request(request),
        )
        return ok(
            {"deleted": True},
            message="Avatar removido com sucesso.",
            operation_id="delete_customer_avatar",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="delete_customer_avatar")
    except Exception:
        logger.exception("delete_customer_avatar_failed")
        return fail(
            "Erro interno ao remover avatar.",
            500,
            operation_id="delete_customer_avatar",
        )

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, File, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_manage_portfolios,
    can_use_team_scope,
)
from commercial_app.application.use_cases.manage_seller_portfolio import parse_customer_assignments
from commercial_app.composition.commercial_composer import (
    build_delpi_commercial_gateway,
    build_manage_customer_avatar_use_case,
    build_resolve_commercial_customer_scope_service,
)
from commercial_app.core.auth_actor import (
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.schemas.portfolio_schemas import EnrichmentBody

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
        scope_service = build_resolve_commercial_customer_scope_service()
        scope = _customer_scope_for_request(request)
        allowed_pairs = scope_service.filter_pairs(
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


@router.get(
    "/{customer_code}/{customer_store}/avatar",
    operation_id="get_customer_avatar",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_customer_avatar(
    request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        scope = _customer_scope_for_request(request)
        build_resolve_commercial_customer_scope_service().ensure_allows(
            scope,
            customer_code=customer_code,
            customer_store=customer_store,
        )
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
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
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
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def delete_customer_avatar(
    _request: Request,
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        build_manage_customer_avatar_use_case().delete(
            customer_code=customer_code,
            customer_store=customer_store,
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

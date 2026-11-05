"""Consultas JWT — histórico MyWEG Necessidades (filial 02)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import (
    build_myweg_needs_compare_service,
    build_myweg_needs_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    MyWegNeedsBatchNotFound,
    MyWegNeedsValidationFailed,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/myweg/need-batches", tags=["MyWEG needs"])


@router.get("", operation_id="list_myweg_need_batches")
def list_myweg_need_batches(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, alias="pageSize", ge=1, le=100),
):
    user = resolve_user(request)
    try:
        data = build_myweg_needs_service().list_batches(
            user, page=page, page_size=pageSize
        )
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get("/latest", operation_id="get_latest_myweg_need_batch")
def get_latest_myweg_need_batch(request: Request):
    user = resolve_user(request)
    try:
        data = build_myweg_needs_service().get_latest_batch(user)
    except MyWegNeedsBatchNotFound as exc:
        return fail(str(exc), 404)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get("/compare", operation_id="compare_myweg_need_batches")
def compare_myweg_need_batches(
    request: Request,
    fromBatchId: str | None = Query(None, alias="fromBatchId"),
    toBatchId: str | None = Query(None, alias="toBatchId"),
    billingMode: str = Query("none", alias="billingMode"),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, alias="pageSize", ge=1, le=200),
    changesOnly: bool = Query(True, alias="changesOnly"),
):
    """Evolução do planejamento entre dois snapshots — faturamento só indicativo."""
    user = resolve_user(request)
    try:
        data = build_myweg_needs_compare_service().compare(
            user,
            from_batch_id=fromBatchId,
            to_batch_id=toBatchId,
            billing_mode=billingMode,
            product_search=search,
            page=page,
            page_size=pageSize,
            changes_only=changesOnly,
        )
    except MyWegNeedsBatchNotFound as exc:
        return fail(str(exc), 404)
    except MyWegNeedsValidationFailed as exc:
        status = 422
        issue_codes = {i.get("code") for i in (exc.issues or [])}
        if "insufficient_batches" in issue_codes or "insufficient_operational_days" in issue_codes:
            status = 409
        return fail(str(exc), status, data={"issues": exc.issues})
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get("/{batchId}", operation_id="get_myweg_need_batch")
def get_myweg_need_batch(request: Request, batchId: str):
    user = resolve_user(request)
    try:
        data = build_myweg_needs_service().get_batch(user, batch_id=batchId)
    except MyWegNeedsBatchNotFound as exc:
        return fail(str(exc), 404)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get("/{batchId}/items", operation_id="list_myweg_need_batch_items")
def list_myweg_need_batch_items(
    request: Request,
    batchId: str,
    search: str = Query(""),
    remessaFrom: date | None = Query(None, alias="remessaFrom"),
    remessaTo: date | None = Query(None, alias="remessaTo"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, alias="pageSize", ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_myweg_needs_service().list_batch_items(
            user,
            batch_id=batchId,
            search=search,
            remessa_from=remessaFrom,
            remessa_to=remessaTo,
            page=page,
            page_size=pageSize,
        )
    except MyWegNeedsBatchNotFound as exc:
        return fail(str(exc), 404)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)

"""Consultas JWT — observações MyWEG NF Emitidas (filial 02)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import (
    build_myweg_invoice_observations_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    MyWegInvoiceObservationNotFound,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(
    prefix="/myweg/invoice-observations",
    tags=["MyWEG invoice observations"],
)


@router.get("", operation_id="list_myweg_invoice_observations")
def list_myweg_invoice_observations(
    request: Request,
    documentDate: date | None = Query(None, alias="documentDate"),
    observationStatus: str | None = Query(None, alias="observationStatus"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, alias="pageSize", ge=1, le=100),
):
    user = resolve_user(request)
    try:
        data = build_myweg_invoice_observations_service().list_observations(
            user,
            document_date=documentDate,
            observation_status=observationStatus,
            page=page,
            page_size=pageSize,
        )
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get(
    "/{observationId}",
    operation_id="get_myweg_invoice_observation",
)
def get_myweg_invoice_observation(request: Request, observationId: str):
    user = resolve_user(request)
    try:
        data = build_myweg_invoice_observations_service().get_observation(
            user, observation_id=observationId
        )
    except MyWegInvoiceObservationNotFound as exc:
        return fail(str(exc), 404)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get(
    "/{observationId}/items",
    operation_id="list_myweg_invoice_observation_items",
)
def list_myweg_invoice_observation_items(
    request: Request,
    observationId: str,
    search: str = Query(""),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, alias="pageSize", ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_myweg_invoice_observations_service().list_observation_items(
            user,
            observation_id=observationId,
            search=search,
            page=page,
            page_size=pageSize,
        )
    except MyWegInvoiceObservationNotFound as exc:
        return fail(str(exc), 404)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)

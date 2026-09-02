from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_freight_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(prefix="/freight", tags=["Freight"])


@router.get("/dashboard")
def get_dashboard(
    request: Request,
    branch: str | None = Query(None),
    issueStart: str | None = Query(None),
    issueEnd: str | None = Query(None),
    entryStart: str | None = Query(None),
    entryEnd: str | None = Query(None),
    supplier: str | None = Query(None),
    invoiceDocument: str | None = Query(None),
    freightDocument: str | None = Query(None),
    situation: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(25),
    sortBy: str | None = Query(None),
    sortDir: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_freight_service().dashboard(
            resolve_user(request),
            branch=branch,
            issue_start=issueStart,
            issue_end=issueEnd,
            entry_start=entryStart,
            entry_end=entryEnd,
            supplier=supplier,
            invoice_document=invoiceDocument,
            freight_document=freightDocument,
            situation=situation,
            page=page,
            page_size=pageSize,
            sort_by=sortBy,
            sort_dir=sortDir,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/inconsistencies")
def get_inconsistencies(
    request: Request,
    branch: str | None = Query(None),
    issueStart: str | None = Query(None),
    issueEnd: str | None = Query(None),
    entryStart: str | None = Query(None),
    entryEnd: str | None = Query(None),
    supplier: str | None = Query(None),
    invoiceDocument: str | None = Query(None),
    freightDocument: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(25),
    refresh: bool = Query(False),
):
    try:
        data = build_freight_service().inconsistencies(
            resolve_user(request),
            branch=branch,
            issue_start=issueStart,
            issue_end=issueEnd,
            entry_start=entryStart,
            entry_end=entryEnd,
            supplier=supplier,
            invoice_document=invoiceDocument,
            freight_document=freightDocument,
            page=page,
            page_size=pageSize,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

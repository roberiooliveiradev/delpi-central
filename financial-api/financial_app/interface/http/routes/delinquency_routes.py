from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_delinquency_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(prefix="/delinquency", tags=["Delinquency"])


@router.get("/dashboard")
def get_dashboard(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    customerCode: str | None = Query(None),
    store: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(20),
    sortBy: str | None = Query(None),
    sortDir: str | None = Query(None),
    onlyWithDelays: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().dashboard(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            customer_code=customerCode,
            store_code=store,
            page=page,
            page_size=pageSize,
            sort_by=sortBy,
            sort_dir=sortDir,
            only_with_delays=onlyWithDelays,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/summary")
def get_summary(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    customerCode: str | None = Query(None),
    store: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().summary(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            customer_code=customerCode,
            store_code=store,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/monthly")
def get_monthly(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    customerCode: str | None = Query(None),
    store: str | None = Query(None),
    newBusinessOnly: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().monthly(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            customer_code=customerCode,
            store_code=store,
            new_business_only=newBusinessOnly,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/aging")
def get_aging(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    customerCode: str | None = Query(None),
    store: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().aging(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            customer_code=customerCode,
            store_code=store,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/customers")
def get_customers(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(20),
    sortBy: str | None = Query(None),
    sortDir: str | None = Query(None),
    search: str | None = Query(None),
    onlyWithDelays: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().customers(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            page=page,
            page_size=pageSize,
            sort_by=sortBy,
            sort_dir=sortDir,
            search=search,
            only_with_delays=onlyWithDelays,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/titles")
def get_titles(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    customerCode: str | None = Query(None),
    store: str | None = Query(None),
    status: str | None = Query(None),
    delayRange: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(20),
    sortBy: str | None = Query(None),
    sortDir: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_delinquency_service().titles(
            resolve_user(request),
            start_date=startDate,
            end_date=endDate,
            customer_code=customerCode,
            store_code=store,
            status=status,
            delay_range=delayRange,
            search=search,
            page=page,
            page_size=pageSize,
            sort_by=sortBy,
            sort_dir=sortDir,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

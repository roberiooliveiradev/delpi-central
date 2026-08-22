from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_cost_center_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(prefix="/cost-centers", tags=["Cost centers"])


@router.get("/filters")
def get_filters(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    costCenter: str | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().filters(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            cost_center=costCenter,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/summary")
def get_summary(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    costCenter: str | None = Query(None),
    supplierCode: str | None = Query(None),
    supplierStore: str | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().summary(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            cost_center=costCenter,
            supplier_code=supplierCode,
            supplier_store=supplierStore,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/series")
def get_series(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    costCenter: str | None = Query(None),
    supplierCode: str | None = Query(None),
    supplierStore: str | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().series(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            cost_center=costCenter,
            supplier_code=supplierCode,
            supplier_store=supplierStore,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/ranking-cost-centers")
def get_ranking_cost_centers(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    supplierCode: str | None = Query(None),
    supplierStore: str | None = Query(None),
    limit: int | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().ranking_cost_centers(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            supplier_code=supplierCode,
            supplier_store=supplierStore,
            limit=limit,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/ranking-suppliers")
def get_ranking_suppliers(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    costCenter: str | None = Query(None),
    limit: int | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().ranking_suppliers(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            cost_center=costCenter,
            limit=limit,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/entries")
def get_entries(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    costCenter: str | None = Query(None),
    supplierCode: str | None = Query(None),
    supplierStore: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(50),
    sortBy: str | None = Query(None),
    sortDir: str | None = Query(None),
    excludeMpProducts: bool = Query(False),
    refresh: bool = Query(False),
):
    try:
        data = build_cost_center_service().entries(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            cost_center=costCenter,
            supplier_code=supplierCode,
            supplier_store=supplierStore,
            search=search,
            page=page,
            page_size=pageSize,
            sort_by=sortBy,
            sort_dir=sortDir,
            exclude_mp_products=excludeMpProducts,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

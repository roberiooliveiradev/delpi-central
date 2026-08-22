from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_indicators_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(prefix="/indicators", tags=["Indicators"])


@router.get("/department")
def get_department(
    request: Request,
    branch: str | None = Query(None),
    competence: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_indicators_service().department(
            resolve_user(request),
            branch=branch,
            competence=competence,
            start_date=startDate,
            end_date=endDate,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.get("/global")
def get_global(
    request: Request,
    branch: str | None = Query(None),
    competence: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_indicators_service().global_score(
            resolve_user(request),
            branch=branch,
            competence=competence,
            start_date=startDate,
            end_date=endDate,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

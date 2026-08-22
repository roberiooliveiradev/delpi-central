from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_overview_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(tags=["Overview"])


@router.get("/overview")
def get_overview(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_overview_service().build(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

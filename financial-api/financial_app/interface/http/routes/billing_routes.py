from __future__ import annotations

from fastapi import APIRouter, Query, Request

from financial_app.composition.financial_composer import build_billing_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.route_errors import fail_from_exception

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/dashboard")
def get_dashboard(
    request: Request,
    branch: str | None = Query(None),
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    granularity: str | None = Query(None),
    refresh: bool = Query(False),
):
    try:
        data = build_billing_service().dashboard(
            resolve_user(request),
            branch=branch,
            start_date=startDate,
            end_date=endDate,
            granularity=granularity,
            refresh=refresh,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

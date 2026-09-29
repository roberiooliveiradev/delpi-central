from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request

from delpi_mes_app.composition.composer import build_mes_read_service
from delpi_mes_app.core.responses import ok
from delpi_mes_app.core.security import (
    MES_DOWNTIMES_VIEW,
    MES_HISTORY_VIEW,
    MES_MONITORING_VIEW,
)
from delpi_mes_app.interface.http.route_errors import fail_from_exception

router = APIRouter(tags=["Delpi MES"])
logger = logging.getLogger(__name__)


@router.get("/monitoring", operation_id="get_delpi_mes_monitoring")
def get_monitoring(request: Request, branch: str = Query(..., min_length=2, max_length=2)):
    try:
        data = build_mes_read_service().get_monitoring(
            request.state.user, branch=branch, permission=MES_MONITORING_VIEW
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info("delpi_mes_monitoring_read branch=%s item_count=%s", branch, len(data["items"]))
    return ok(data)


@router.get("/runs/{run_id}/timeline", operation_id="get_delpi_mes_run_timeline")
def get_timeline(request: Request, run_id: str):
    try:
        data = build_mes_read_service().get_timeline(
            request.state.user, run_id, permission=MES_HISTORY_VIEW
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info("delpi_mes_timeline_read run_id=%s item_count=%s", run_id, len(data["items"]))
    return ok(data)


@router.get("/downtimes", operation_id="list_delpi_mes_downtimes")
def get_downtimes(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str | None = Query(default=None, alias="workCenter", max_length=40),
    period_from: datetime | None = Query(default=None, alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, alias="pageSize", ge=1, le=100),
):
    try:
        data = build_mes_read_service().get_downtimes(
            request.state.user,
            branch=branch,
            work_center=work_center,
            period_from=period_from,
            period_to=period_to,
            page=page,
            page_size=page_size,
            permission=MES_DOWNTIMES_VIEW,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_read branch=%s page=%s page_size=%s item_count=%s",
        branch, page, page_size, len(data["items"]),
    )
    return ok(data)

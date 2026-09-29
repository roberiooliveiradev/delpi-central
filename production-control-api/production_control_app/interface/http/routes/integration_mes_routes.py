from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request

from delpi_auth.service_token import request_has_valid_internal_service_token
from production_control_app.composition.pc_composer import build_mes_integration_read_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import InvalidBranch, ProductionRunNotFound

router = APIRouter(prefix="/integrations/mes", tags=["MES integrations"])
logger = logging.getLogger(__name__)


def _deny_unless_internal(request: Request):
    if request_has_valid_internal_service_token(request):
        return None
    return fail("Credencial de serviço interno inválida ou ausente.", 401)


def _aware(value: datetime | None, name: str) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{name} deve incluir timezone.")
    return value


def _error(exc: Exception):
    if isinstance(exc, ProductionRunNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, (InvalidBranch, ValueError)):
        return fail(str(exc), 422)
    raise exc


@router.get("/work-centers/live", operation_id="get_mes_live_work_centers")
def get_live_work_centers(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().get_live_work_centers(branch=branch)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_integration_live_read branch=%s item_count=%s", branch, len(data["items"]))
    return ok(data)


@router.get("/runs/{run_id}/timeline", operation_id="get_mes_integration_run_timeline")
def get_run_timeline(request: Request, run_id: str):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().get_run_timeline(run_id)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_integration_timeline_read run_id=%s item_count=%s", run_id, len(data["items"]))
    return ok(data)


@router.get("/downtimes", operation_id="list_mes_integration_downtimes")
def list_downtimes(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str | None = Query(default=None, alias="workCenter", max_length=40),
    period_from: datetime | None = Query(default=None, alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, alias="pageSize", ge=1, le=100),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().list_downtimes(
            branch=branch,
            work_center=work_center,
            period_from=_aware(period_from, "from"),
            period_to=_aware(period_to, "to"),
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_read branch=%s page=%s page_size=%s item_count=%s",
        branch,
        page,
        page_size,
        len(data["items"]),
    )
    return ok(data)

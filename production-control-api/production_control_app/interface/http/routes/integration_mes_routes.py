from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from delpi_auth.service_token import request_has_valid_internal_service_token
from production_control_app.composition.pc_composer import (
    build_mes_downtime_reason_admin_service,
    build_mes_integration_read_service,
    build_mes_run_performance_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    DowntimeReasonConflict,
    DowntimeReasonNotFound,
    InvalidBranch,
    InvalidDowntimeReason,
    ProductionRunNotFound,
)

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


class DowntimeReasonCreateBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    code: str = Field(..., min_length=1, max_length=40)
    label: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=1, max_length=40)
    requires_note: bool = Field(..., alias="requiresNote")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)


class DowntimeReasonUpdateBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    label: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=1, max_length=40)
    requires_note: bool = Field(..., alias="requiresNote")
    sort_order: int = Field(default=0, alias="sortOrder", ge=0)


class DowntimeReasonActiveBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    active: bool


def _error(exc: Exception):
    if isinstance(exc, ProductionRunNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DowntimeReasonNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DowntimeReasonConflict):
        return fail(str(exc), 409)
    if isinstance(exc, (InvalidDowntimeReason, InvalidBranch, ValueError)):
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


@router.get(
    "/work-centers/{work_center}/timeline",
    operation_id="get_mes_integration_work_center_timeline",
)
def get_work_center_timeline(
    request: Request,
    work_center: str,
    branch: str = Query(..., min_length=2, max_length=2),
    period_from: datetime = Query(..., alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().get_work_center_timeline(
            branch=branch,
            work_center=work_center,
            period_from=_aware(period_from, "from"),
            period_to=_aware(period_to, "to"),
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_work_center_timeline_read branch=%s work_center=%s item_count=%s",
        branch,
        work_center,
        len(data["items"]),
    )
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


_PERFORMANCE_FIELDS = (
    "idealCycleSeconds", "producedPieces", "producingSeconds",
    "idealProductionSeconds", "performancePercent",
    "actualAverageCycleSeconds", "actualThroughputPerHour",
    "expectedThroughputPerHour", "dataQuality",
    "standardTimeSource", "standardTimeDataQuality",
)


@router.get("/runs/{run_id}/performance", operation_id="get_mes_integration_run_performance")
def get_run_performance(request: Request, run_id: str):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_run_performance_service().get_run_performance(run_id)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_integration_performance_read run_id=%s", run_id)
    return ok(
        {
            "runId": data["runId"],
            "branch": data.get("branch"),
            "workCenter": data.get("workCenter"),
            "status": data.get("status"),
            "referenceAt": data.get("referenceAt"),
            "performance": {
                field: data.get(field) for field in _PERFORMANCE_FIELDS
            },
        }
    )


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


@router.get("/downtime-reasons", operation_id="list_mes_downtime_reasons")
def list_downtime_reasons(request: Request):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_reason_admin_service().list_reasons()
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_downtime_reasons_admin_list item_count=%s", len(data["items"]))
    return ok(data)


@router.post("/downtime-reasons", operation_id="create_mes_downtime_reason")
def create_downtime_reason(request: Request, body: DowntimeReasonCreateBody):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_reason_admin_service().create_reason(
            code=body.code,
            label=body.label,
            category=body.category,
            requires_note=body.requires_note,
            sort_order=body.sort_order,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_downtime_reason_admin_create code=%s", data["code"])
    return ok(data, status_code=201)


@router.put("/downtime-reasons/{code}", operation_id="update_mes_downtime_reason")
def update_downtime_reason(request: Request, code: str, body: DowntimeReasonUpdateBody):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_reason_admin_service().update_reason(
            code,
            label=body.label,
            category=body.category,
            requires_note=body.requires_note,
            sort_order=body.sort_order,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_downtime_reason_admin_update code=%s", data["code"])
    return ok(data)


@router.patch(
    "/downtime-reasons/{code}/active",
    operation_id="set_mes_downtime_reason_active",
)
def set_downtime_reason_active(request: Request, code: str, body: DowntimeReasonActiveBody):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_reason_admin_service().set_reason_active(
            code, active=body.active
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info("mes_downtime_reason_admin_active code=%s active=%s", data["code"], data["active"])
    return ok(data)

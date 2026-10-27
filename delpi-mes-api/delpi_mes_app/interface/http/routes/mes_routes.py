from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from delpi_mes_app.composition.composer import (
    build_mes_downtime_management_service,
    build_mes_downtime_reason_admin_service,
    build_mes_read_service,
)
from delpi_mes_app.core.responses import ok
from delpi_mes_app.core.security import (
    MES_DOWNTIMES_VIEW,
    MES_HISTORY_VIEW,
    MES_MONITORING_VIEW,
)
from delpi_mes_app.interface.http.route_errors import fail_from_exception

router = APIRouter(tags=["Delpi MES"])
logger = logging.getLogger(__name__)


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


@router.get("/runs/{run_id}/performance", operation_id="get_delpi_mes_run_performance")
def get_run_performance(request: Request, run_id: str):
    try:
        data = build_mes_read_service().get_run_performance(
            request.state.user, run_id, permission=MES_MONITORING_VIEW
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info("delpi_mes_performance_read run_id=%s", run_id)
    return ok(data)


@router.get(
    "/work-centers/{work_center}/timeline",
    operation_id="get_delpi_mes_work_center_timeline",
)
def get_work_center_timeline(
    request: Request,
    work_center: str,
    branch: str = Query(..., min_length=2, max_length=2),
    period_from: datetime | None = Query(default=None, alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
):
    try:
        data = build_mes_read_service().get_work_center_timeline(
            request.state.user,
            work_center=work_center,
            branch=branch,
            period_from=period_from,
            period_to=period_to,
            permission=MES_HISTORY_VIEW,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_work_center_timeline_read branch=%s work_center=%s item_count=%s",
        branch, work_center, len(data["items"]),
    )
    return ok(data)


@router.get(
    "/downtimes/filter-options",
    operation_id="list_delpi_mes_downtime_filter_options",
)
def get_downtime_filter_options(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
):
    try:
        data = build_mes_read_service().get_downtime_filter_options(
            request.state.user,
            branch=branch,
            permission=MES_DOWNTIMES_VIEW,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_filter_options_read branch=%s reasons=%s sources=%s",
        branch,
        len(data["reasons"]),
        len(data["sources"]),
    )
    return ok(data)


@router.get(
    "/downtimes/analytics",
    operation_id="get_delpi_mes_downtime_analytics",
)
def get_downtime_analytics(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    period_from: datetime = Query(..., alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
    work_center: str | None = Query(default=None, alias="workCenter", max_length=40),
    reason_code: str | None = Query(default=None, alias="reasonCode", max_length=40),
    source: str | None = Query(default=None, max_length=40),
    classification: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=10),
):
    try:
        data = build_mes_read_service().get_downtime_analytics(
            request.state.user,
            branch=branch,
            period_from=period_from,
            period_to=period_to,
            work_center=work_center,
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
            permission=MES_DOWNTIMES_VIEW,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_analytics_read branch=%s occurrences=%s",
        branch,
        data.get("summary", {}).get("occurrencesCount"),
    )
    return ok(data)


@router.get("/downtimes", operation_id="list_delpi_mes_downtimes")
def get_downtimes(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str | None = Query(default=None, alias="workCenter", max_length=40),
    period_from: datetime | None = Query(default=None, alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
    reason_code: str | None = Query(default=None, alias="reasonCode", max_length=40),
    source: str | None = Query(default=None, max_length=40),
    classification: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=10),
    sort: str | None = Query(default=None, max_length=10),
    downtime_id: str | None = Query(default=None, alias="downtimeId", max_length=40),
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
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
            sort=sort,
            downtime_id=downtime_id,
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


@router.get(
    "/registrations/downtime-reasons",
    operation_id="list_delpi_mes_downtime_reasons",
)
def list_downtime_reasons(request: Request):
    try:
        data = build_mes_downtime_reason_admin_service().list_reasons(
            request.state.user
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_reason_list item_count=%s", len(data["items"])
    )
    return ok(data)


@router.post(
    "/registrations/downtime-reasons",
    operation_id="create_delpi_mes_downtime_reason",
)
def create_downtime_reason(request: Request, body: DowntimeReasonCreateBody):
    try:
        data = build_mes_downtime_reason_admin_service().create_reason(
            request.state.user,
            code=body.code,
            label=body.label,
            category=body.category,
            requires_note=body.requires_note,
            sort_order=body.sort_order,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info("delpi_mes_downtime_reason_created code=%s", data["code"])
    return ok(data, status_code=201)


@router.put(
    "/registrations/downtime-reasons/{code}",
    operation_id="update_delpi_mes_downtime_reason",
)
def update_downtime_reason(
    request: Request, code: str, body: DowntimeReasonUpdateBody
):
    try:
        data = build_mes_downtime_reason_admin_service().update_reason(
            request.state.user,
            code,
            label=body.label,
            category=body.category,
            requires_note=body.requires_note,
            sort_order=body.sort_order,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info("delpi_mes_downtime_reason_updated code=%s", data["code"])
    return ok(data)


@router.patch(
    "/registrations/downtime-reasons/{code}/active",
    operation_id="set_delpi_mes_downtime_reason_active",
)
def set_downtime_reason_active(
    request: Request, code: str, body: DowntimeReasonActiveBody
):
    try:
        data = build_mes_downtime_reason_admin_service().set_reason_active(
            request.state.user, code, active=body.active
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_reason_active_changed code=%s active=%s",
        data["code"], data["active"],
    )
    return ok(data)


class DowntimeClassifyBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    reason_code: str = Field(..., alias="reasonCode", min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=500)
    expected_updated_at: str = Field(..., alias="expectedUpdatedAt", min_length=1)


class DowntimeTreatmentUpsertBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    analysis: str = Field(..., min_length=1, max_length=2000)
    cause_kind: str = Field(..., alias="causeKind", min_length=1, max_length=20)
    cause_note: str | None = Field(default=None, alias="causeNote", max_length=500)
    action_needed: bool = Field(..., alias="actionNeeded")
    justification: str = Field(..., min_length=1, max_length=2000)
    expected_updated_at: str | None = Field(
        default=None, alias="expectedUpdatedAt"
    )


class DowntimeReferralBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    issue_code: str = Field(..., alias="issueCode", min_length=1, max_length=60)
    note: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(
        default=None, alias="idempotencyKey", max_length=120
    )


class DowntimeConclusionBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    reason: str = Field(..., min_length=1, max_length=2000)


@router.post(
    "/downtimes/{downtime_id}/classification",
    operation_id="classify_delpi_mes_downtime",
)
def classify_downtime(
    request: Request, downtime_id: str, body: DowntimeClassifyBody
):
    try:
        data = build_mes_downtime_management_service().classify_downtime(
            request.state.user,
            downtime_id,
            branch=body.branch,
            reason_code=body.reason_code,
            note=body.note,
            expected_updated_at=body.expected_updated_at,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_classified downtime=%s reason=%s",
        downtime_id,
        data.get("reasonCode"),
    )
    return ok(data)


@router.get(
    "/downtimes/{downtime_id}/treatment",
    operation_id="get_delpi_mes_downtime_treatment",
)
def get_downtime_treatment(
    request: Request,
    downtime_id: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    try:
        data = build_mes_downtime_management_service().get_treatment(
            request.state.user, downtime_id, branch=branch
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)


@router.put(
    "/downtimes/{downtime_id}/treatment",
    operation_id="upsert_delpi_mes_downtime_treatment",
)
def upsert_downtime_treatment(
    request: Request, downtime_id: str, body: DowntimeTreatmentUpsertBody
):
    try:
        data = build_mes_downtime_management_service().upsert_treatment(
            request.state.user,
            downtime_id,
            branch=body.branch,
            analysis=body.analysis,
            cause_kind=body.cause_kind,
            cause_note=body.cause_note,
            action_needed=body.action_needed,
            justification=body.justification,
            expected_updated_at=body.expected_updated_at,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_treatment_saved downtime=%s", downtime_id
    )
    return ok(data)


@router.post(
    "/downtimes/{downtime_id}/treatment/referrals",
    operation_id="refer_delpi_mes_downtime",
)
def refer_downtime(
    request: Request, downtime_id: str, body: DowntimeReferralBody
):
    try:
        data = build_mes_downtime_management_service().refer_request(
            request.state.user,
            downtime_id,
            branch=body.branch,
            issue_code=body.issue_code,
            note=body.note,
            idempotency_key=body.idempotency_key,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_referred downtime=%s", downtime_id
    )
    return ok(data)


@router.post(
    "/downtimes/{downtime_id}/treatment/conclusion",
    operation_id="conclude_delpi_mes_downtime_treatment",
)
def conclude_downtime_treatment(
    request: Request, downtime_id: str, body: DowntimeConclusionBody
):
    try:
        data = build_mes_downtime_management_service().conclude_treatment(
            request.state.user,
            downtime_id,
            branch=body.branch,
            reason=body.reason,
        )
    except Exception as exc:
        return fail_from_exception(exc)
    logger.info(
        "delpi_mes_downtime_treatment_concluded downtime=%s", downtime_id
    )
    return ok(data)


@router.get(
    "/downtimes/{downtime_id}/history",
    operation_id="get_delpi_mes_downtime_history",
)
def get_downtime_history(
    request: Request,
    downtime_id: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    try:
        data = build_mes_downtime_management_service().get_history(
            request.state.user, downtime_id, branch=branch
        )
    except Exception as exc:
        return fail_from_exception(exc)
    return ok(data)

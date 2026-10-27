from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from delpi_auth.service_token import request_has_valid_internal_service_token
from production_control_app.composition.pc_composer import (
    build_mes_downtime_classification_service,
    build_mes_downtime_reason_admin_service,
    build_mes_downtime_treatment_service,
    build_mes_integration_read_service,
    build_mes_run_performance_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    DowntimeConflict,
    DowntimeNotFound,
    DowntimeReasonConflict,
    DowntimeReasonNotFound,
    DowntimeTreatmentConflict,
    DowntimeTreatmentNotFound,
    InvalidBranch,
    InvalidDowntimeReason,
    InvalidMesEvent,
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
    if isinstance(exc, (DowntimeNotFound, DowntimeTreatmentNotFound)):
        return fail(str(exc), 404)
    if isinstance(exc, (DowntimeConflict, DowntimeTreatmentConflict)):
        return fail(str(exc), 409)
    if isinstance(
        exc, (InvalidDowntimeReason, InvalidMesEvent, InvalidBranch, ValueError)
    ):
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
    reason_code: str | None = Query(default=None, alias="reasonCode", max_length=40),
    source: str | None = Query(default=None, max_length=40),
    classification: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=10),
    sort: str | None = Query(default=None, max_length=10),
    downtime_id: str | None = Query(default=None, alias="downtimeId", max_length=40),
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
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
            sort=sort,
            downtime_id=downtime_id,
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


@router.get(
    "/downtimes/analytics",
    operation_id="get_mes_integration_downtime_analytics",
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
    # Agregações gerenciais de paradas (Etapa 2): mesmo universo elegível
    # da listagem, calculado no owner MES — paginação/sort/downtimeId não
    # são determinantes de métrica e nem são aceitos aqui.
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().get_downtime_analytics(
            branch=branch,
            work_center=work_center,
            period_from=_aware(period_from, "from"),
            period_to=_aware(period_to, "to"),
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_analytics_read branch=%s occurrences=%s "
        "overlap=%s partial=%s",
        branch,
        data["summary"]["occurrencesCount"],
        data["quality"]["overlapDetected"],
        data["quality"]["partial"],
    )
    return ok(data)


@router.get("/downtimes/export", operation_id="export_mes_integration_downtimes")
def export_downtimes(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    work_center: str | None = Query(default=None, alias="workCenter", max_length=40),
    period_from: datetime | None = Query(default=None, alias="from"),
    period_to: datetime | None = Query(default=None, alias="to"),
    reason_code: str | None = Query(default=None, alias="reasonCode", max_length=40),
    source: str | None = Query(default=None, max_length=40),
    classification: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=10),
    pendency: bool = Query(default=False),
):
    # Exportação gerencial (Etapa 5): fatos completos do mesmo universo
    # elegível da listagem — paginação/sort/downtimeId não se aplicam.
    # pendency=true restringe ao relatório de pendências.
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().export_downtimes(
            branch=branch,
            work_center=work_center,
            period_from=_aware(period_from, "from"),
            period_to=_aware(period_to, "to"),
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
            pendency=pendency,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_export branch=%s total=%s items=%s capped=%s",
        branch,
        data["total"],
        len(data["items"]),
        data["capped"],
    )
    return ok(data)


@router.get("/downtimes/insights", operation_id="get_mes_integration_downtime_insights")
def get_downtime_insights(
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
    # Análise avançada (Etapa 6): reincidência, comparação de períodos,
    # criticidade parametrizada, eficácia de ações e pendências sobre o
    # mesmo universo elegível da listagem/analytics.
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().get_downtime_insights(
            branch=branch,
            work_center=work_center,
            period_from=_aware(period_from, "from"),
            period_to=_aware(period_to, "to"),
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_insights branch=%s critical_items=%s "
        "telemetry_gaps=%s",
        branch,
        len(data["critical"]["items"]),
        len(data["quality"]["telemetryGaps"]),
    )
    return ok(data)


@router.get("/downtime-sources", operation_id="list_mes_integration_downtime_sources")
def list_downtime_sources(request: Request):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_integration_read_service().list_downtime_sources()
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_sources_read item_count=%s",
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


class DowntimeClassifyBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    reason_code: str = Field(..., alias="reasonCode", min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=500)
    expected_updated_at: datetime = Field(..., alias="expectedUpdatedAt")
    actor_ref: str = Field(..., alias="actorRef", min_length=1, max_length=120)
    actor_name: str = Field(..., alias="actorName", min_length=1, max_length=160)


class DowntimeTreatmentUpsertBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    analysis: str = Field(..., min_length=1, max_length=2000)
    cause_kind: str = Field(..., alias="causeKind", min_length=1, max_length=20)
    cause_note: str | None = Field(default=None, alias="causeNote", max_length=500)
    action_needed: bool = Field(..., alias="actionNeeded")
    justification: str = Field(..., min_length=1, max_length=2000)
    expected_updated_at: datetime | None = Field(
        default=None, alias="expectedUpdatedAt"
    )
    actor_ref: str = Field(..., alias="actorRef", min_length=1, max_length=120)
    actor_name: str = Field(..., alias="actorName", min_length=1, max_length=160)


class DowntimeRequestLinkBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    request_id: str = Field(..., alias="requestId", min_length=1, max_length=60)
    request_type_code: str = Field(
        ..., alias="requestTypeCode", min_length=1, max_length=80
    )
    actor_ref: str = Field(..., alias="actorRef", min_length=1, max_length=120)
    actor_name: str = Field(..., alias="actorName", min_length=1, max_length=160)


class DowntimeConclusionBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    branch: str = Field(..., min_length=2, max_length=2)
    reason: str = Field(..., min_length=1, max_length=2000)
    linked_request_completed: bool = Field(
        default=False, alias="linkedRequestCompleted"
    )
    actor_ref: str = Field(..., alias="actorRef", min_length=1, max_length=120)
    actor_name: str = Field(..., alias="actorName", min_length=1, max_length=160)


@router.post(
    "/downtimes/{downtime_id}/classification",
    operation_id="classify_mes_integration_downtime",
)
def classify_downtime(
    request: Request, downtime_id: str, body: DowntimeClassifyBody
):
    """Classificação gerencial da parada — autorização humana no BFF.

    O ator chega resolvido (BFF já validou o usuário humano + permissões);
    aqui vale a filial contra a parada e a precondição otimista.
    """
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_classification_service().classify_managed(
            downtime_id,
            branch=body.branch,
            reason_code=body.reason_code,
            note=body.note,
            expected_updated_at=body.expected_updated_at,
            actor_ref=body.actor_ref,
            actor_name=body.actor_name,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_classified downtime=%s reason=%s actor=%s",
        downtime_id,
        data["reasonCode"],
        body.actor_ref,
    )
    return ok(data)


@router.get(
    "/downtimes/{downtime_id}/treatment",
    operation_id="get_mes_integration_downtime_treatment",
)
def get_downtime_treatment(
    request: Request,
    downtime_id: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_treatment_service().get_treatment(
            downtime_id, branch=branch
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return ok({"treatment": data})


@router.put(
    "/downtimes/{downtime_id}/treatment",
    operation_id="upsert_mes_integration_downtime_treatment",
)
def upsert_downtime_treatment(
    request: Request, downtime_id: str, body: DowntimeTreatmentUpsertBody
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_treatment_service().upsert_treatment(
            downtime_id,
            branch=body.branch,
            analysis=body.analysis,
            cause_kind=body.cause_kind,
            cause_note=body.cause_note,
            action_needed=body.action_needed,
            justification=body.justification,
            expected_updated_at=body.expected_updated_at,
            actor_ref=body.actor_ref,
            actor_name=body.actor_name,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_treatment_saved downtime=%s status=%s",
        downtime_id,
        data["status"],
    )
    return ok(data)


@router.post(
    "/downtimes/{downtime_id}/treatment/request-link",
    operation_id="link_mes_integration_downtime_request",
)
def link_downtime_request(
    request: Request, downtime_id: str, body: DowntimeRequestLinkBody
):
    """Vincula a solicitação criada no requests-api — idempotente por id."""
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_treatment_service().link_request(
            downtime_id,
            branch=body.branch,
            request_id=body.request_id,
            request_type_code=body.request_type_code,
            actor_ref=body.actor_ref,
            actor_name=body.actor_name,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_request_linked downtime=%s request=%s",
        downtime_id,
        body.request_id,
    )
    return ok(data)


@router.post(
    "/downtimes/{downtime_id}/treatment/conclusion",
    operation_id="conclude_mes_integration_downtime_treatment",
)
def conclude_downtime_treatment(
    request: Request, downtime_id: str, body: DowntimeConclusionBody
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_mes_downtime_treatment_service().conclude(
            downtime_id,
            branch=body.branch,
            reason=body.reason,
            linked_request_completed=body.linked_request_completed,
            actor_ref=body.actor_ref,
            actor_name=body.actor_name,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    logger.info(
        "mes_integration_downtime_treatment_concluded downtime=%s", downtime_id
    )
    return ok(data)


@router.get(
    "/downtimes/{downtime_id}/history",
    operation_id="get_mes_integration_downtime_history",
)
def get_downtime_history(
    request: Request,
    downtime_id: str,
    branch: str = Query(..., min_length=2, max_length=2),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        items = build_mes_downtime_treatment_service().history(
            downtime_id, branch=branch
        )
    except Exception as exc:  # noqa: BLE001
        return _error(exc)
    return ok({"items": items})

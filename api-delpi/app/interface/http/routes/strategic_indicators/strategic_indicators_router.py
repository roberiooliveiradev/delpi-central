"""BFF Strategic Indicators — user-parity READ routes (DAVI governed surface).

These routes are the bounded cross-API adapter consumed by the DAVI semantic
``read`` tool (and any future governed surface). They forward the caller's own
JWT to ``strategic-indicators-api`` user-facing routes; the internal service
token is never attached, so the SI backend remains the authority for
``strategic-indicators.*`` authorization (fail-closed).

READ-only by contract: only GET handlers exist here. No mutation, cache
invalidation, job dispatch or configuration import is reachable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import HTTPException
from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.security.api_delpi_permissions import (
    STRATEGIC_INDICATORS_SETTINGS_MANAGE,
    STRATEGIC_INDICATORS_TRENDS_VIEW,
    STRATEGIC_INDICATORS_VIEW,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.application.services.strategic_indicators.si_client_error_policy import (
    is_si_not_found_error,
)
from app.application.services.strategic_indicators.si_user_parity_service import (
    StrategicIndicatorsUserParityService,
)
from app.interface.http.openapi_agent_metadata import (
    SI_ADMIN_CONFIG_EXPORT,
    SI_ADMIN_DEPARTMENTS,
    SI_ADMIN_DEPARTMENT_INDICATORS,
    SI_ALERTS,
    SI_CACHE_REFRESH_STATUS,
    SI_CHANGE_REQUESTS,
    SI_DEPARTMENTS,
    SI_DEPARTMENTS_TREE,
    SI_DEPARTMENTS_TREE_SNAPSHOT,
    SI_DEPARTMENTS_TREE_TRENDS,
    SI_DEPARTMENT_DETAILS,
    SI_EXECUTIVE_SUMMARY,
    SI_GOAL_YEARS_OVERVIEW,
    SI_INDICATOR_GOALS,
    SI_INDICATOR_GOAL_HISTORY,
    SI_INDICATORS,
    SI_JOB_STATUS,
    SI_PRESENTATION,
    SI_SETTINGS,
    SI_SETTINGS_AUDIT,
    SI_TRENDS,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    SI_DEPARTMENT_ID_QUERY_OPTIONAL,
)
from delpi_auth.authorization import require_permission

router = APIRouter(
    prefix="/strategic-indicators",
    tags=["strategic-indicators"],
)

GET_SI_EXECUTIVE_SUMMARY = "get_si_executive_summary"
GET_SI_DEPARTMENTS = "get_si_departments"
GET_SI_INDICATORS = "get_si_indicators"
LIST_SI_INDICATOR_GOALS = "list_si_indicator_goals"
LIST_SI_INDICATOR_GOAL_HISTORY = "list_si_indicator_goal_history"
GET_SI_DEPARTMENT_DETAILS = "get_si_department_details"
GET_SI_DEPARTMENTS_TREE = "get_si_departments_tree"
GET_SI_DEPARTMENTS_TREE_SNAPSHOT = "get_si_departments_tree_snapshot"
GET_SI_DEPARTMENTS_TREE_TRENDS = "get_si_departments_tree_trends"
GET_SI_ALERTS = "get_si_alerts"
GET_SI_TRENDS = "get_si_trends"
GET_SI_PRESENTATION = "get_si_presentation"
GET_SI_CACHE_REFRESH_STATUS = "get_si_cache_refresh_status"
GET_SI_JOB_STATUS = "get_si_job_status"
GET_SI_SETTINGS = "get_si_settings"
LIST_SI_SETTINGS_AUDIT = "list_si_settings_audit"
LIST_SI_CHANGE_REQUESTS = "list_si_change_requests"
LIST_SI_ADMIN_DEPARTMENTS = "list_si_admin_departments"
LIST_SI_ADMIN_DEPARTMENT_INDICATORS = "list_si_admin_department_indicators"
LIST_SI_GOAL_YEARS_OVERVIEW = "list_si_goal_years_overview"
EXPORT_SI_ADMIN_CONFIG = "export_si_admin_config"


def _si_user_parity_service() -> StrategicIndicatorsUserParityService:
    from app.application.services.strategic_indicators.si_user_parity_service import (
        get_si_user_parity_service,
    )

    return get_si_user_parity_service()


def _user_authorization(request: Request) -> str:
    return request.headers.get("authorization") or ""


def _map_si_error(exc: StrategicIndicatorsApiError) -> HTTPException:
    status = exc.status_code
    if status in (401, 403):
        return HTTPException(status_code=status, detail=str(exc))
    if status == 404 or is_si_not_found_error(exc):
        return HTTPException(status_code=404, detail=str(exc))
    if status is not None and 400 <= status < 500:
        return HTTPException(
            status_code=502,
            detail=f"Resposta inesperada da Strategic Indicators API ({status}).",
        )
    return HTTPException(
        status_code=503,
        detail="Strategic Indicators API indisponível no momento.",
    )


@router.get(
    "/executive-summary",
    **SI_EXECUTIVE_SUMMARY,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_executive_summary(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = Query(
        default=None, description="Competence reference in YYYY-MM format."
    ),
    start_date: str | None = Query(
        default=None,
        description="Optional period start date filter in YYYY-MM-DD format.",
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional period end date filter in YYYY-MM-DD format.",
    ),
):
    try:
        payload = service.get_executive_summary(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_EXECUTIVE_SUMMARY)


@router.get(
    "/departments",
    **SI_DEPARTMENTS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_departments(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = Query(
        default=None, description="Competence reference in YYYY-MM format."
    ),
    start_date: str | None = Query(
        default=None,
        description="Optional period start date filter in YYYY-MM-DD format.",
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional period end date filter in YYYY-MM-DD format.",
    ),
):
    try:
        payload = service.get_departments(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_DEPARTMENTS)


@router.get(
    "/indicators",
    **SI_INDICATORS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_indicators(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = Query(
        default=None, description="Competence reference in YYYY-MM format."
    ),
    start_date: str | None = Query(
        default=None,
        description="Optional period start date filter in YYYY-MM-DD format.",
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional period end date filter in YYYY-MM-DD format.",
    ),
):
    try:
        payload = service.get_indicators(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_INDICATORS)


@router.get(
    "/indicator-goals",
    **SI_INDICATOR_GOALS,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_indicator_goals(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    indicator_id: str | None = Query(
        default=None, description="Optional indicator id filter."
    ),
    goal_year: int | None = Query(
        default=None, description="Optional goal year filter (e.g. 2026)."
    ),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    active_only: bool | None = Query(
        default=None,
        description="When true, only active goal versions are returned.",
    ),
):
    try:
        payload = service.list_indicator_goals(
            authorization=_user_authorization(request),
            indicator_id=indicator_id,
            goal_year=goal_year,
            department_id=department_id,
            active_only=active_only,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_INDICATOR_GOALS)


@router.get(
    "/indicator-goals/history",
    **SI_INDICATOR_GOAL_HISTORY,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_indicator_goal_history(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    indicator_id: str = Query(
        ..., description="Indicator id whose goal history is requested."
    ),
    goal_year: int | None = Query(
        default=None, description="Optional goal year filter (e.g. 2026)."
    ),
):
    try:
        payload = service.list_indicator_goal_history(
            authorization=_user_authorization(request),
            indicator_id=indicator_id,
            goal_year=goal_year,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_INDICATOR_GOAL_HISTORY)


_COMPETENCE_QUERY = Query(
    default=None, description="Competence reference in YYYY-MM format."
)
_START_DATE_QUERY = Query(
    default=None,
    description="Optional period start date filter in YYYY-MM-DD format.",
)
_END_DATE_QUERY = Query(
    default=None,
    description="Optional period end date filter in YYYY-MM-DD format.",
)
_MONTHS_QUERY = Query(
    default=None,
    ge=2,
    le=12,
    description="Trend window in months (owner default: 6, range 2-12).",
)
_VIEW_MODE_QUERY = Query(
    default=None,
    description="Tree view mode (owner default: consolidated).",
)


@router.get(
    "/departments/{department_id}",
    **SI_DEPARTMENT_DETAILS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_department_details(
    request: Request,
    department_id: str,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
):
    try:
        payload = service.get_department_details(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_DEPARTMENT_DETAILS)


@router.get(
    "/departments-tree",
    **SI_DEPARTMENTS_TREE,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_departments_tree(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    view_mode: str | None = _VIEW_MODE_QUERY,
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
    months: int | None = _MONTHS_QUERY,
):
    try:
        payload = service.get_departments_tree(
            authorization=_user_authorization(request),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_DEPARTMENTS_TREE)


@router.get(
    "/departments-tree/snapshot",
    **SI_DEPARTMENTS_TREE_SNAPSHOT,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_departments_tree_snapshot(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    view_mode: str | None = _VIEW_MODE_QUERY,
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
):
    try:
        payload = service.get_departments_tree_snapshot(
            authorization=_user_authorization(request),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(
        payload, operation_id=GET_SI_DEPARTMENTS_TREE_SNAPSHOT
    )


@router.get(
    "/departments-tree/trends",
    **SI_DEPARTMENTS_TREE_TRENDS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_departments_tree_trends(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    view_mode: str | None = _VIEW_MODE_QUERY,
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
    months: int | None = _MONTHS_QUERY,
):
    try:
        payload = service.get_departments_tree_trends(
            authorization=_user_authorization(request),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_DEPARTMENTS_TREE_TRENDS)


@router.get(
    "/alerts",
    **SI_ALERTS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_alerts(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
):
    try:
        payload = service.get_alerts(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_ALERTS)


@router.get(
    "/trends",
    **SI_TRENDS,
)
@require_permission(STRATEGIC_INDICATORS_TRENDS_VIEW)
def get_si_trends(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    department_id: str | None = SI_DEPARTMENT_ID_QUERY_OPTIONAL(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
    months: int | None = _MONTHS_QUERY,
):
    try:
        payload = service.get_trends(
            authorization=_user_authorization(request),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_TRENDS)


@router.get(
    "/presentation",
    **SI_PRESENTATION,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_presentation(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    competence: str | None = _COMPETENCE_QUERY,
    start_date: str | None = _START_DATE_QUERY,
    end_date: str | None = _END_DATE_QUERY,
    months: int | None = _MONTHS_QUERY,
    include: str | None = Query(
        default=None,
        description=(
            "Comma-separated sections: executive_summary, "
            "departments_overview, department_details_by_id, "
            "indicators_by_department_id, alerts, trends."
        ),
    ),
):
    try:
        payload = service.get_presentation(
            authorization=_user_authorization(request),
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
            include=include,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_PRESENTATION)


@router.get(
    "/cache-refresh/status",
    **SI_CACHE_REFRESH_STATUS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_cache_refresh_status(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    include: str | None = Query(
        default=None,
        description="Optional comma-separated top-level response keys to include.",
    ),
):
    try:
        payload = service.get_cache_refresh_status(
            authorization=_user_authorization(request),
            include=include,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_CACHE_REFRESH_STATUS)


@router.get(
    "/jobs/{job_id}",
    **SI_JOB_STATUS,
)
@require_permission(STRATEGIC_INDICATORS_VIEW)
def get_si_job_status(
    request: Request,
    job_id: str,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
):
    try:
        payload = service.get_job_status(
            authorization=_user_authorization(request),
            job_id=job_id,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_JOB_STATUS)


@router.get(
    "/settings",
    **SI_SETTINGS,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def get_si_settings(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    include: str | None = Query(
        default=None,
        description=(
            "Optional comma-separated settings sections to include "
            "(weights, goals, parameters, governance, meta)."
        ),
    ),
):
    try:
        payload = service.get_settings(
            authorization=_user_authorization(request),
            include=include,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=GET_SI_SETTINGS)


@router.get(
    "/settings/audit",
    **SI_SETTINGS_AUDIT,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_settings_audit(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Max audit rows (owner default: 20)."
    ),
    entity_key: str | None = Query(
        default=None, description="Optional audit entity key filter."
    ),
):
    try:
        payload = service.list_settings_audit(
            authorization=_user_authorization(request),
            limit=limit,
            entity_key=entity_key,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_SETTINGS_AUDIT)


@router.get(
    "/change-requests",
    **SI_CHANGE_REQUESTS,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_change_requests(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Max rows (owner default: 100)."
    ),
    offset: int | None = Query(
        default=None, ge=0, description="Pagination offset."
    ),
):
    try:
        payload = service.list_change_requests(
            authorization=_user_authorization(request),
            limit=limit,
            offset=offset,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_CHANGE_REQUESTS)


@router.get(
    "/admin/departments",
    **SI_ADMIN_DEPARTMENTS,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_admin_departments(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Max rows (BFF-side pagination)."
    ),
    offset: int | None = Query(
        default=None, ge=0, description="Pagination offset (BFF-side)."
    ),
):
    try:
        payload = service.list_admin_departments(
            authorization=_user_authorization(request),
            limit=limit,
            offset=offset,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_ADMIN_DEPARTMENTS)


@router.get(
    "/admin/departments/{department_id}/indicators",
    **SI_ADMIN_DEPARTMENT_INDICATORS,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_admin_department_indicators(
    request: Request,
    department_id: str,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Max rows (BFF-side pagination)."
    ),
    offset: int | None = Query(
        default=None, ge=0, description="Pagination offset (BFF-side)."
    ),
):
    try:
        payload = service.list_admin_department_indicators(
            authorization=_user_authorization(request),
            department_id=department_id,
            limit=limit,
            offset=offset,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(
        payload, operation_id=LIST_SI_ADMIN_DEPARTMENT_INDICATORS
    )


@router.get(
    "/admin/goal-years/overview",
    **SI_GOAL_YEARS_OVERVIEW,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def list_si_goal_years_overview(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    limit: int | None = Query(
        default=None, ge=1, le=200, description="Max rows (BFF-side pagination)."
    ),
    offset: int | None = Query(
        default=None, ge=0, description="Pagination offset (BFF-side)."
    ),
):
    try:
        payload = service.list_goal_years_overview(
            authorization=_user_authorization(request),
            limit=limit,
            offset=offset,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=LIST_SI_GOAL_YEARS_OVERVIEW)


@router.get(
    "/admin/config/bundle",
    **SI_ADMIN_CONFIG_EXPORT,
)
@require_permission(STRATEGIC_INDICATORS_SETTINGS_MANAGE)
def export_si_admin_config(
    request: Request,
    service: StrategicIndicatorsUserParityService = Depends(_si_user_parity_service),
    include: str | None = Query(
        default=None,
        description=(
            "Optional comma-separated export sections to include "
            "(BFF-side scope selection; omit for the full bundle)."
        ),
    ),
):
    try:
        payload = service.export_admin_config(
            authorization=_user_authorization(request),
            include=include,
        )
    except StrategicIndicatorsApiError as exc:
        raise _map_si_error(exc) from exc
    return api_delpi_success(payload, operation_id=EXPORT_SI_ADMIN_CONFIG)

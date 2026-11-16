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
    SI_DEPARTMENTS,
    SI_EXECUTIVE_SUMMARY,
    SI_INDICATOR_GOALS,
    SI_INDICATOR_GOAL_HISTORY,
    SI_INDICATORS,
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

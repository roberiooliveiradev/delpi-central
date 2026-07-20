from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    DASHBOARD_COMMERCIAL_VIEW,
    DASHBOARD_ENGINEERING_VIEW,
    DASHBOARD_FINANCIAL_VIEW,
    DASHBOARD_HR_VIEW,
    DASHBOARD_LMPS_VIEW,
    DASHBOARD_PRODUCTION_VIEW,
    DASHBOARD_QUALITY_VIEW,
    DASHBOARD_SUPPLIES_VIEW,
    API_DELPI_ACCESS,
    API_DELPI_QUALITY_ACCESS,
)
from app.application.services.strategic_indicators.dashboard_department_idd_service import (
    get_dashboard_department_idd_service,
)
from app.interface.http.route_response_helpers import api_delpi_success

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DASHBOARD_IDD_ACCESS = sorted(
    {
        API_DELPI_ACCESS,
        API_DELPI_QUALITY_ACCESS,
        DASHBOARD_COMMERCIAL_VIEW,
        DASHBOARD_ENGINEERING_VIEW,
        DASHBOARD_FINANCIAL_VIEW,
        DASHBOARD_HR_VIEW,
        DASHBOARD_LMPS_VIEW,
        DASHBOARD_PRODUCTION_VIEW,
        DASHBOARD_QUALITY_VIEW,
        DASHBOARD_SUPPLIES_VIEW,
    }
)

ALLOWED_DEPARTMENT_IDS = frozenset(
    {
        "commercial",
        "hr",
        "production",
        "financial",
        "supplies",
        "engineering",
        "quality",
    }
)
_DEPARTMENT_ID_ENUM = sorted(ALLOWED_DEPARTMENT_IDS)


@router.get(
    "/department-idd",
    operation_id="get_dashboard_department_idd",
    summary="Department IDD score",
    description="Strategic Indicators department score for dashboards.",
)
@require_any_permission(DASHBOARD_IDD_ACCESS)
def get_dashboard_department_idd(
    department_id: str = Query(
        ...,
        description="SI department id.",
        enum=_DEPARTMENT_ID_ENUM,
    ),
    competence: str | None = Query(
        default=None,
        description="Reference month as YYYY-MM.",
    ),
    start_date: str | None = Query(
        default=None,
        description="Period start (YYYY-MM-DD).",
    ),
    end_date: str | None = Query(
        default=None,
        description="Period end (YYYY-MM-DD).",
    ),
    branch: str | None = Query(
        default=None,
        description="Branch code (optional).",
    ),
):
    normalized_id = department_id.strip().lower()
    if normalized_id not in ALLOWED_DEPARTMENT_IDS:
        raise HTTPException(
            status_code=422,
            detail="department_id inválido para consulta de IDD departamental.",
        )

    item = get_dashboard_department_idd_service().get_department_idd(
        department_id=normalized_id,
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        competence=competence,
    )

    return api_delpi_success(
        {"item": item},
        operation_id="get_dashboard_department_idd",
        entity="dashboard_department_idd",
        shape="scalar",
        message="IDD departamental consultado com sucesso",
    )

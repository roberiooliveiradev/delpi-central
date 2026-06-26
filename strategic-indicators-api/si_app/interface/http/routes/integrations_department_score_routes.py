from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from si_app.composition.strategic_indicators_composer import (
    build_get_dashboard_department_score_use_case,
)

router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-department-score",
    tags=["Strategic Indicators Integrações"],
)


@router.get("")
def get_dashboard_department_score(
    department_id: str = Query(
        ...,
        description="Identificador do departamento no SI (ex.: commercial, quality).",
    ),
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    try:
        use_case = build_get_dashboard_department_score_use_case()
        payload = use_case.execute(
            department_id=department_id,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        if payload is None:
            return {"item": None}
        return {"item": payload}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao resolver IDD departamental para dashboards: {exc}",
        ) from exc

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from si_app.composition.strategic_indicators_composer import (
    build_get_dashboard_department_indicators_use_case,
    build_get_dashboard_departments_indicators_use_case,
)

department_indicators_router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-department-indicators",
    tags=["Strategic Indicators Integrações"],
)

departments_indicators_router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-departments-indicators",
    tags=["Strategic Indicators Integrações"],
)


@department_indicators_router.get("")
def get_dashboard_department_indicators(
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
        use_case = build_get_dashboard_department_indicators_use_case()
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
            detail=(
                "Falha ao resolver IDD/metas/realizado do departamento "
                f"para dashboards: {exc}"
            ),
        ) from exc


@departments_indicators_router.get("")
def get_dashboard_departments_indicators(
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    department_id: str | None = Query(
        default=None,
        description="Opcional: filtra um departamento.",
    ),
):
    try:
        use_case = build_get_dashboard_departments_indicators_use_case()
        return use_case.execute(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            department_id=department_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Falha ao listar departamentos com IDD/metas/realizado "
                f"para dashboards: {exc}"
            ),
        ) from exc

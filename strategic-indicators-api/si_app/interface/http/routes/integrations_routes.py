from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from si_app.composition.strategic_indicators_composer import (
    build_get_dashboard_goals_by_source_keys_use_case,
)

router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-goals",
    tags=["Strategic Indicators Integrações"],
)


@router.get("")
def list_dashboard_goals(
    source_keys: str = Query(
        ...,
        description="Chaves de integração separadas por vírgula (department_indicators.source_key).",
    ),
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    department_id: str | None = Query(default=None),
):
    try:
        keys = [part.strip() for part in source_keys.split(",") if part.strip()]
        use_case = build_get_dashboard_goals_by_source_keys_use_case()
        items = use_case.execute(
            source_keys=keys,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            department_id=department_id,
        )
        return {"items": items}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao resolver metas para dashboards: {exc}",
        ) from exc

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from si_app.composition.strategic_indicators_composer import (
    build_get_dashboard_indicator_metric_use_case,
)

realized_router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-indicator-realized",
    tags=["Strategic Indicators Integrações"],
)

meta_router = APIRouter(
    prefix="/strategic-indicators/integrations/dashboard-indicator-meta",
    tags=["Strategic Indicators Integrações"],
)


def _execute_metric(
    *,
    kind: str,
    indicator_id: str,
    competence: str | None,
    start_date: str | None,
    end_date: str | None,
    branch: str | None,
) -> dict:
    try:
        use_case = build_get_dashboard_indicator_metric_use_case()
        payload = use_case.execute(
            indicator_id=indicator_id,
            kind=kind,  # type: ignore[arg-type]
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        if payload is None:
            raise HTTPException(
                status_code=404,
                detail=f"Indicador '{indicator_id}' não encontrado no SI.",
            )
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao resolver {kind} do indicador SI: {exc}",
        ) from exc


@realized_router.get("")
def get_dashboard_indicator_realized(
    indicator_id: str = Query(..., description="indicator_id SI (ex.: quality-ppm-internal)."),
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    return _execute_metric(
        kind="realized",
        indicator_id=indicator_id,
        competence=competence,
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )


@meta_router.get("")
def get_dashboard_indicator_meta(
    indicator_id: str = Query(..., description="indicator_id SI (ex.: quality-ppm-internal)."),
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    return _execute_metric(
        kind="meta",
        indicator_id=indicator_id,
        competence=competence,
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )

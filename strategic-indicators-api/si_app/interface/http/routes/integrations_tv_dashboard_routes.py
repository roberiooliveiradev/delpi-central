from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from si_app.application.dto.strategic_indicators.get_executive_summary_real_request import (
    GetExecutiveSummaryRealRequest,
)
from si_app.composition.strategic_indicators_composer import (
    build_get_strategic_indicators_executive_summary_use_case,
)

router = APIRouter(
    prefix="/strategic-indicators/integrations/tv-dashboard-hero",
    tags=["Strategic Indicators Integrações"],
)


@router.get("")
def get_tv_dashboard_hero(
    branch: str | None = Query(default=None),
    competence: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        raw = build_get_strategic_indicators_executive_summary_use_case().execute(
            GetExecutiveSummaryRealRequest(
                branch=branch,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
            )
        )
        departments = raw.get("departments") if isinstance(raw.get("departments"), list) else []
        scored = [item for item in departments if isinstance(item, dict)]
        sorted_by_score = sorted(
            scored,
            key=lambda item: float(item.get("score") or 0),
            reverse=True,
        )
        best = sorted_by_score[0] if sorted_by_score else None
        worst = sorted_by_score[-1] if sorted_by_score else None
        variation = raw.get("variation") if isinstance(raw.get("variation"), dict) else {}

        return {
            "competence": raw.get("competence"),
            "igd": raw.get("igd"),
            "classification": raw.get("classification"),
            "trendDirection": variation.get("direction"),
            "bestDepartment": (best or {}).get("name"),
            "primaryRisk": (worst or {}).get("name"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar hero TV do Strategic Indicators: {exc}",
        ) from exc

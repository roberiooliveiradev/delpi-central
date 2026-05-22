from __future__ import annotations

from typing import Any

from app.utils.logger import log_error


def enrich_dashboard_metric(
    payload: dict[str, Any],
    *,
    source_key: str,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    department_id: str | None = None,
    recompute_target_pct_from: str | None = None,
    summary_key: str | None = None,
) -> dict[str, Any]:
    try:
        from app.application.services.strategic_indicators.dashboard_goals_service import (
            get_dashboard_goals_service,
        )

        return get_dashboard_goals_service().attach_goal_fields(
            payload,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            department_id=department_id,
            recompute_target_pct_from=recompute_target_pct_from,
            summary_key=summary_key,
        )
    except Exception as exc:
        log_error(
            f"Metas SI não aplicadas para {source_key}: {exc}",
        )
        return payload

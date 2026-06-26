from __future__ import annotations

import time
from typing import Any

from strategic_indicators_client import StrategicIndicatorsApiClient, StrategicIndicatorsApiError

from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
    normalize_si_period_date,
)
from app.utils.logger import log_error


class DashboardDepartmentIddService:
    _CACHE_TTL_SECONDS = 45.0

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()
        self._cache: dict[tuple, tuple[float, dict[str, Any] | None]] = {}

    def get_department_idd(
        self,
        *,
        department_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_id = (department_id or "").strip()
        if not normalized_id:
            return None

        normalized_start = normalize_si_period_date(start_date)
        normalized_end = normalize_si_period_date(end_date)
        normalized_branch = normalize_si_branch(branch)

        cache_key = (
            normalized_id,
            competence or "",
            normalized_start or "",
            normalized_end or "",
            normalized_branch or "",
        )
        now = time.monotonic()
        cached = self._cache.get(cache_key)
        if cached and now - cached[0] < self._CACHE_TTL_SECONDS:
            return cached[1]

        try:
            payload = self._client.get_dashboard_department_score(
                department_id=normalized_id,
                competence=competence,
                start_date=normalized_start,
                end_date=normalized_end,
                branch=normalized_branch,
            )
        except StrategicIndicatorsApiError as exc:
            log_error(
                "dashboard_department_idd_fetch_failed",
                extra={
                    "department_id": normalized_id,
                    "error": str(exc),
                },
            )
            self._cache[cache_key] = (now, None)
            return None

        item = payload.get("item") if isinstance(payload, dict) else None
        resolved = item if isinstance(item, dict) else None
        self._cache[cache_key] = (now, resolved)
        return resolved


_department_idd_service: DashboardDepartmentIddService | None = None


def get_dashboard_department_idd_service() -> DashboardDepartmentIddService:
    global _department_idd_service
    if _department_idd_service is None:
        _department_idd_service = DashboardDepartmentIddService()
    return _department_idd_service

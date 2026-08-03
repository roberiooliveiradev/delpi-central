"""IGD (Índice Global DELPI) via S2S TV hero do Strategic Indicators."""

from __future__ import annotations

import time
from typing import Any

from strategic_indicators_client import StrategicIndicatorsApiClient, StrategicIndicatorsApiError

from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
    normalize_si_period_date,
)
from app.utils.logger import log_error


class DashboardIgdService:
    """Busca o hero consolidado (IGD) para dashboards / reports."""

    _CACHE_TTL_SECONDS = 45.0

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()
        self._cache: dict[tuple, tuple[float, dict[str, Any] | None]] = {}

    def get_igd(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_start = normalize_si_period_date(start_date)
        normalized_end = normalize_si_period_date(end_date)
        normalized_branch = normalize_si_branch(branch)
        cache_key = (
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
            payload = self._client.get_tv_dashboard_hero(
                competence=competence,
                start_date=normalized_start,
                end_date=normalized_end,
                branch=normalized_branch,
            )
        except StrategicIndicatorsApiError as exc:
            log_error(
                f"dashboard_igd_fetch_failed competence={competence or ''} error={exc}"
            )
            self._cache[cache_key] = (now, None)
            return None

        if not isinstance(payload, dict):
            self._cache[cache_key] = (now, None)
            return None

        resolved = {
            "igd": payload.get("igd"),
            "classification": payload.get("classification"),
            "trendDirection": payload.get("trendDirection"),
            "bestDepartment": payload.get("bestDepartment"),
            "primaryRisk": payload.get("primaryRisk"),
            "competence": payload.get("competence") or competence,
        }
        self._cache[cache_key] = (now, resolved)
        return resolved


_igd_service: DashboardIgdService | None = None


def get_dashboard_igd_service() -> DashboardIgdService:
    global _igd_service
    if _igd_service is None:
        _igd_service = DashboardIgdService()
    return _igd_service

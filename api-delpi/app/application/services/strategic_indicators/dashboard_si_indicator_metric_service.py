from __future__ import annotations

import time
from typing import Any, Literal

from strategic_indicators_client import StrategicIndicatorsApiClient, StrategicIndicatorsApiError

from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
    normalize_si_period_date,
)
from app.utils.logger import log_error

MetricKind = Literal["realized", "meta"]


class DashboardSiIndicatorMetricService:
    _CACHE_TTL_SECONDS = 45.0

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()
        self._cache: dict[tuple, tuple[float, Any]] = {}

    def get_metric(
        self,
        *,
        indicator_id: str,
        kind: MetricKind,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
    ) -> dict[str, Any] | None:
        normalized_id = (indicator_id or "").strip()
        if not normalized_id:
            return None

        normalized_start = normalize_si_period_date(start_date)
        normalized_end = normalize_si_period_date(end_date)
        normalized_branch = normalize_si_branch(branch)
        cache_key = (
            kind,
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
            if kind == "realized":
                payload = self._client.get_dashboard_indicator_realized(
                    indicator_id=normalized_id,
                    competence=competence,
                    start_date=normalized_start,
                    end_date=normalized_end,
                    branch=normalized_branch,
                )
            else:
                payload = self._client.get_dashboard_indicator_meta(
                    indicator_id=normalized_id,
                    competence=competence,
                    start_date=normalized_start,
                    end_date=normalized_end,
                    branch=normalized_branch,
                )
        except StrategicIndicatorsApiError as exc:
            message = str(exc)
            if "404" in message or "não encontrado" in message.lower():
                self._cache[cache_key] = (now, None)
                return None
            log_error(
                "dashboard_si_indicator_metric_fetch_failed",
                extra={
                    "indicator_id": normalized_id,
                    "kind": kind,
                    "error": message,
                },
            )
            self._cache[cache_key] = (now, None)
            return None

        resolved = payload if isinstance(payload, dict) else None
        self._cache[cache_key] = (now, resolved)
        return resolved


_si_indicator_metric_service: DashboardSiIndicatorMetricService | None = None


def get_dashboard_si_indicator_metric_service() -> DashboardSiIndicatorMetricService:
    global _si_indicator_metric_service
    if _si_indicator_metric_service is None:
        _si_indicator_metric_service = DashboardSiIndicatorMetricService()
    return _si_indicator_metric_service

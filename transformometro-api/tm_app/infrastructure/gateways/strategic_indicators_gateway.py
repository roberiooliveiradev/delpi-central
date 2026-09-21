"""HTTP adapter to the public Strategic Indicators integrations API."""

from __future__ import annotations

import logging
import os
from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)

logger = logging.getLogger(__name__)


def _timeout_seconds() -> float:
    raw = os.getenv("STRATEGIC_INDICATORS_API_TIMEOUT", "8")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 8.0
    return max(1.0, min(value, 30.0))


class StrategicIndicatorsGateway:
    """Fail-closed consumer of the shared SI public client."""

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient(
            timeout_seconds=_timeout_seconds()
        )

    def get_department_score(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any] | None:
        try:
            payload = self._client.get_dashboard_department_score(
                department_id=department_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        except StrategicIndicatorsApiError as exc:
            logger.warning(
                "tm_si_department_score_unavailable department_id=%s error=%s",
                department_id,
                exc,
            )
            return None
        item = payload.get("item") if isinstance(payload, dict) else None
        return item if isinstance(item, dict) else None

    def get_department_indicators(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any] | None:
        try:
            payload = self._client.get_dashboard_department_indicators(
                department_id=department_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        except StrategicIndicatorsApiError as exc:
            logger.warning(
                "tm_si_department_indicators_unavailable department_id=%s error=%s",
                department_id,
                exc,
            )
            return None
        item = payload.get("item") if isinstance(payload, dict) else None
        return item if isinstance(item, dict) else None

    def list_dashboard_goals(
        self,
        *,
        source_keys: list[str],
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        department_id: str | None,
    ) -> dict[str, Any] | None:
        try:
            payload = self._client.list_dashboard_goals(
                source_keys=source_keys,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                department_id=department_id,
            )
        except StrategicIndicatorsApiError as exc:
            logger.warning("tm_si_dashboard_goals_unavailable error=%s", exc)
            return None
        return payload if isinstance(payload, dict) else None

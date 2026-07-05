from __future__ import annotations

from typing import Any

from delpi_auth.service_token import internal_service_authorization
from strategic_indicators_client.client import StrategicIndicatorsApiClient

from tv_app.application.services.tv_dashboard_content_service import (
    message,
    trend_direction_label,
)


class StrategicIndicatorsGateway:
    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    def fetch_hero(
        self,
        *,
        branch: str | None,
        competence: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        payload = self._client.get_tv_dashboard_hero(
            branch=branch,
            competence=competence,
            authorization=authorization or internal_service_authorization(),
        )
        direction = str(payload.get("trendDirection") or "stable")
        return {
            "branch": branch,
            "competence": payload.get("competence"),
            "igd": payload.get("igd"),
            "classification": payload.get("classification"),
            "trendDirection": direction,
            "trendLabel": trend_direction_label(direction),
            "bestDepartment": payload.get("bestDepartment"),
            "primaryRisk": payload.get("primaryRisk"),
            "label": message("strategicHeroLabel", "Índice Global Delpi"),
        }

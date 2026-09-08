from __future__ import annotations

import logging
from typing import Any

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope

logger = logging.getLogger("supplies-api.strategic_indicators")

# Canonical SI indicator ids for supplies department (dashboard-supplies).
SI_INDICATOR_BY_KPI = {
    "KPI-OTD": "supplies-otd",
    "KPI-STOCK-VALUE": "supplies-stock-value",
    "KPI-TURNOVER": "supplies-stock-turnover",
    "KPI-CPV": "supplies-cpv",
    "KPI-SAVINGS": "supplies-negotiation-savings",
}


class StrategicIndicatorsGatewayError(RuntimeError):
    pass


class StrategicIndicatorsGateway:
    """Reads SI metas via api-delpi dashboard department-indicators (platform path)."""

    def __init__(self, delpi: DelpiApiGateway | None = None) -> None:
        self.delpi = delpi or DelpiApiGateway()

    def goals_by_kpi(
        self,
        *,
        access_token: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, float | None]:
        params: dict[str, Any] = {"department_id": "supplies"}
        if branch:
            params["branch"] = branch
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            raw = self.delpi.get(
                "/dashboard/department-indicators",
                access_token=access_token,
                params=params,
            )
        except Exception as exc:  # noqa: BLE001 — degrade to empty metas
            logger.warning("si_goals_unavailable error=%s", exc)
            raise StrategicIndicatorsGatewayError("strategic indicators unavailable") from exc

        data = unwrap_delpi_envelope(raw)
        item = data.get("item") if isinstance(data, dict) else None
        indicators = item.get("indicators") if isinstance(item, dict) else None
        by_id: dict[str, Any] = {}
        if isinstance(indicators, list):
            for row in indicators:
                if isinstance(row, dict) and row.get("indicator_id"):
                    by_id[str(row["indicator_id"])] = row

        goals: dict[str, float | None] = {}
        for kpi_id, indicator_id in SI_INDICATOR_BY_KPI.items():
            row = by_id.get(indicator_id) or {}
            score = row.get("score")
            try:
                goals[kpi_id] = float(score) if score is not None else None
            except (TypeError, ValueError):
                goals[kpi_id] = None
        return goals

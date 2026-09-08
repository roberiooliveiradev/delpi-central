from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.gateways.strategic_indicators_gateway import (
    SI_INDICATOR_BY_KPI,
    StrategicIndicatorsGateway,
)


def test_metrics_by_kpi_maps_goal_value_and_score_not_score_as_meta():
    delpi = MagicMock()
    delpi.get.return_value = {
        "item": {
            "indicators": [
                {
                    "indicator_id": "supplies-otd",
                    "goal_value": 98.0,
                    "score": 6.57,
                },
                {
                    "indicator_id": "supplies-stock-value",
                    "goal_value": 1_000_000.0,
                    "score": 8.2,
                },
            ]
        }
    }
    gateway = StrategicIndicatorsGateway(delpi=delpi)
    metrics = gateway.metrics_by_kpi(
        access_token="t",
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    assert metrics["KPI-OTD"] == {"goal": 98.0, "score": 6.57}
    assert metrics["KPI-STOCK-VALUE"] == {"goal": 1_000_000.0, "score": 8.2}
    assert gateway.goals_by_kpi(
        access_token="t",
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )["KPI-OTD"] == 98.0
    assert set(metrics) == set(SI_INDICATOR_BY_KPI)

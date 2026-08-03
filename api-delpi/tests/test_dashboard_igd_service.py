"""Unit — DashboardIgdService (TV hero S2S)."""

from __future__ import annotations

from unittest.mock import MagicMock

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.services.strategic_indicators.dashboard_igd_service import (
    DashboardIgdService,
)


def test_get_igd_returns_hero_fields() -> None:
    mock_client = MagicMock()
    mock_client.get_tv_dashboard_hero.return_value = {
        "competence": "2026-06",
        "igd": 7.8,
        "classification": "Bom",
        "trendDirection": "up",
        "bestDepartment": "Comercial",
        "primaryRisk": "Qualidade",
    }
    service = DashboardIgdService(client=mock_client)

    result = service.get_igd(competence="2026-06")

    assert result == {
        "igd": 7.8,
        "classification": "Bom",
        "trendDirection": "up",
        "bestDepartment": "Comercial",
        "primaryRisk": "Qualidade",
        "competence": "2026-06",
    }
    mock_client.get_tv_dashboard_hero.assert_called_once_with(
        competence="2026-06",
        start_date=None,
        end_date=None,
        branch=None,
    )


def test_get_igd_returns_none_on_api_error() -> None:
    mock_client = MagicMock()
    mock_client.get_tv_dashboard_hero.side_effect = StrategicIndicatorsApiError("down")
    service = DashboardIgdService(client=mock_client)

    assert service.get_igd(competence="2026-06") is None

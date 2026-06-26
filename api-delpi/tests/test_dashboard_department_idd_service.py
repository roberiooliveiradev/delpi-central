from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.strategic_indicators.dashboard_department_idd_service import (
    DashboardDepartmentIddService,
)


def test_get_department_idd_returns_item_from_client() -> None:
    mock_client = MagicMock()
    mock_client.get_dashboard_department_score.return_value = {
        "item": {
            "department_id": "commercial",
            "score": 8.1,
            "classification": "Excelência",
        }
    }
    service = DashboardDepartmentIddService(client=mock_client)

    result = service.get_department_idd(
        department_id="commercial",
        start_date="2026-06-01",
        end_date="2026-06-30",
        branch="1",
    )

    assert result == {
        "department_id": "commercial",
        "score": 8.1,
        "classification": "Excelência",
    }
    mock_client.get_dashboard_department_score.assert_called_once_with(
        department_id="commercial",
        competence=None,
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )

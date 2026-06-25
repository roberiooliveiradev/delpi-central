from unittest.mock import MagicMock

from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.models.page import Page
from app.application.use_cases.production.get_production_oee_use_case import (
    GetProductionOeeUseCase,
)


def test_get_production_oee_use_case_returns_summary_and_appointments():
    repository = MagicMock()
    repository.get_oee_appointments_bundle.return_value = (
        {
            "total_appointments": 100,
            "valid_appointments": 95,
            "outlier_appointments": 5,
            "avg_oee_pct_by_branch": {"01": 72.5},
        },
        Page(
            items=[
                {
                    "branch": "01",
                    "production_order": "000123",
                    "status": "valid",
                    "oee_pct": 80.0,
                }
            ],
            total=1,
            page=1,
            page_size=20,
        ),
    )

    use_case = GetProductionOeeUseCase(repository)
    result = use_case.execute(
        GetProductionOeeRequest(
            branch="01",
            start_date="2024-01-01",
            end_date="2024-01-31",
            page=1,
            page_size=20,
        )
    )

    assert result["summary"]["oee_pct"] == 72.5
    assert result["summary"]["total_appointments"] == 100
    assert result["summary"]["valid_appointments"] == 95
    assert result["summary"]["outlier_appointments"] == 5
    assert result["summary"]["outlier_percentage"] == 5.0
    assert result["appointments"]["total"] == 1
    assert result["appointments"]["items"][0]["status"] == "valid"
    repository.get_oee_appointments_bundle.assert_called_once()
    repository.get_overall_equipment_effectiveness.assert_not_called()


def test_get_production_oee_use_case_uses_filtered_average_when_scope_filters():
    repository = MagicMock()
    repository.get_oee_appointments_bundle.return_value = (
        {
            "total_appointments": 3,
            "valid_appointments": 2,
            "outlier_appointments": 1,
            "avg_oee_pct": 61.25,
        },
        Page(
            items=[],
            total=0,
            page=1,
            page_size=20,
        ),
    )

    use_case = GetProductionOeeUseCase(repository)
    result = use_case.execute(
        GetProductionOeeRequest(
            branch="01",
            start_date="2024-01-01",
            end_date="2024-01-31",
            production_order="24319401002",
            page=1,
            page_size=20,
        )
    )

    assert result["summary"]["oee_pct"] == 61.25
    repository.get_overall_equipment_effectiveness.assert_not_called()
    repository.get_oee_appointments_bundle.assert_called_once()

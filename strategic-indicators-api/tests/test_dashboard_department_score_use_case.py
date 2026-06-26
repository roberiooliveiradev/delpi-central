from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.use_cases.strategic_indicators.get_dashboard_department_score_use_case import (
    GetDashboardDepartmentScoreUseCase,
)


def test_get_dashboard_department_score_returns_matching_department() -> None:
    departments_use_case = MagicMock()
    departments_use_case.execute.return_value = {
        "items": [
            {
                "id": "quality",
                "name": "Qualidade",
                "score": 7.25,
                "classification": "Alto Desempenho",
                "contribution": 1.2,
                "variation": {"absolute": 0.1, "percent": 1.4},
            }
        ],
        "partial_success": False,
    }

    use_case = GetDashboardDepartmentScoreUseCase(
        departments_use_case=departments_use_case,
    )

    result = use_case.execute(
        department_id="quality",
        competence="2026-06",
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )

    assert result == {
        "department_id": "quality",
        "department_name": "Qualidade",
        "score": 7.25,
        "classification": "Alto Desempenho",
        "contribution": 1.2,
        "variation": {"absolute": 0.1, "percent": 1.4},
        "partial_success": False,
    }


def test_get_dashboard_department_score_returns_none_when_empty() -> None:
    departments_use_case = MagicMock()
    departments_use_case.execute.return_value = {"items": [], "partial_success": False}

    use_case = GetDashboardDepartmentScoreUseCase(
        departments_use_case=departments_use_case,
    )

    assert use_case.execute(department_id="hr") is None

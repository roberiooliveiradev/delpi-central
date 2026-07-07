from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_department_score_use_case import (
    GetDashboardDepartmentScoreUseCase,
)


def _department(
    *,
    department_id: str = "quality",
    score: float = 7.25,
) -> StrategicDepartmentCalculatedValue:
    return StrategicDepartmentCalculatedValue(
        department_id=department_id,
        department_name="Qualidade",
        short_name="Qualidade",
        weight_pct=15.0,
        strategic_summary="",
        aggregation_mode="average_of_units",
        score=score,
        contribution=1.2,
        classification="Alto Desempenho",
        trend="stable",
        indicators=[],
    )


def test_get_dashboard_department_score_returns_matching_department() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_dashboard_department_snapshot.return_value = (
        _department(),
        [],
    )

    use_case = GetDashboardDepartmentScoreUseCase(
        snapshot_service=snapshot_service,
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
        "variation": None,
        "partial_success": False,
    }
    snapshot_service.get_dashboard_department_snapshot.assert_called_once_with(
        department_id="quality",
        competence="2026-06",
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch="01",
    )


def test_get_dashboard_department_score_marks_partial_success_on_errors() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_dashboard_department_snapshot.return_value = (
        _department(department_id="engineering", score=6.8),
        [{"department_id": "engineering", "message": "upstream timeout"}],
    )

    use_case = GetDashboardDepartmentScoreUseCase(
        snapshot_service=snapshot_service,
    )

    result = use_case.execute(department_id="engineering")

    assert result is not None
    assert result["partial_success"] is True


def test_get_dashboard_department_score_returns_none_when_empty() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_dashboard_department_snapshot.return_value = (None, [])

    use_case = GetDashboardDepartmentScoreUseCase(
        snapshot_service=snapshot_service,
    )

    assert use_case.execute(department_id="hr") is None

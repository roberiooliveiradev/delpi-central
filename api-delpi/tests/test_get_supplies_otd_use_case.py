from unittest.mock import MagicMock, patch

from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from app.composition.query_cache_composer import reset_query_cache_for_tests


def _monthly_row(**overrides) -> dict:
    base = {
        "branch": "01",
        "year": 2026,
        "month": 4,
        "month_date": "2026-04-01",
        "total_lines": 100,
        "on_time_lines": 80,
        "late_lines": 20,
        "otd_percentage": 80.0,
    }
    base.update(overrides)
    return base


def test_execute_builds_summary_from_monthly_without_summary_query() -> None:
    repository = MagicMock()
    repository.get_otd_monthly_breakdown.return_value = [
        _monthly_row(total_lines=60, on_time_lines=50, late_lines=10),
        _monthly_row(month_date="2026-05-01", total_lines=40, on_time_lines=30, late_lines=10),
    ]
    repository.get_top_late_suppliers.return_value = []
    repository.get_late_deliveries.return_value = []

    use_case = GetOTDUseCase(repository)
    result = use_case.execute(
        GetOTDRequest(branch="01", start_date="20260401", end_date="20260531"),
    )

    repository.get_otd_summary.assert_not_called()
    assert result["summary"]["total_lines"] == 100
    assert result["summary"]["on_time_lines"] == 80
    assert result["summary"]["late_lines"] == 20
    assert result["summary"]["otd_percentage"] == 80.0
    assert result["start_date"] == "2026-04-01"
    assert result["end_date"] == "2026-05-01"


def test_execute_caches_response_without_second_repository_call() -> None:
    reset_query_cache_for_tests()
    repository = MagicMock()
    repository.get_otd_monthly_breakdown.return_value = [_monthly_row()]
    repository.get_top_late_suppliers.return_value = []
    repository.get_late_deliveries.return_value = []

    use_case = GetOTDUseCase(repository)
    request = GetOTDRequest(start_date="20260401", end_date="20260430")

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first["summary"]["total_lines"] == 100
    assert second == first
    repository.get_otd_monthly_breakdown.assert_called_once()
    repository.get_top_late_suppliers.assert_called_once()
    repository.get_late_deliveries.assert_called_once()


def test_execute_returns_cached_response_without_repository_call() -> None:
    repository = MagicMock()
    use_case = GetOTDUseCase(repository)
    request = GetOTDRequest(start_date="20260401", end_date="20260430")

    cached = {
        "branch": "consolidated",
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
        "summary": {
            "total_lines": 10,
            "on_time_lines": 9,
            "late_lines": 1,
            "otd_percentage": 90.0,
            "late_percentage": 10.0,
        },
        "monthly_breakdown": [],
        "top_late_suppliers": [],
        "late_deliveries": [],
    }

    with patch(
        "app.application.use_cases.supplies.get_otd_use_case.get_cached_supplies_otd",
        return_value=cached,
    ):
        result = use_case.execute(request)

    assert result == cached
    repository.get_otd_monthly_breakdown.assert_not_called()

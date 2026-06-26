from unittest.mock import MagicMock

from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.use_cases.production.get_production_oee_series_use_case import (
    GetProductionOeeSeriesUseCase,
)


def test_production_oee_series_returns_points_per_bucket() -> None:
    repository = MagicMock()
    repository.list_oee_kpi_by_day_and_branch.return_value = [
        {
            "production_date": "2026-05-15",
            "branch": "01",
            "oee_pct": 80.0,
            "appointment_count": 10,
        },
        {
            "production_date": "2026-05-15",
            "branch": "02",
            "oee_pct": 70.0,
            "appointment_count": 8,
        },
    ]

    use_case = GetProductionOeeSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOeeSeriesRequest(
            granularity="month",
            date_start="2026-05-01",
            date_end="2026-05-31",
        )
    )

    assert result.points
    assert result.points[0].oee_filial_01 == 80.0
    assert result.points[0].oee_filial_02 == 70.0
    assert result.branch is None
    repository.list_oee_kpi_by_day_and_branch.assert_called_once()


def test_production_oee_series_treats_empty_oee_as_null() -> None:
    repository = MagicMock()
    repository.list_oee_kpi_by_day_and_branch.return_value = []

    use_case = GetProductionOeeSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOeeSeriesRequest(
            granularity="day",
            date_start="2026-05-01",
            date_end="2026-05-02",
        )
    )

    assert result.points
    assert result.points[0].oee_filial_01 is None
    assert result.points[0].oee_filial_02 is None


def test_production_oee_series_filters_single_branch() -> None:
    repository = MagicMock()
    repository.list_oee_kpi_by_day_and_branch.return_value = [
        {
            "production_date": "2026-05-10",
            "branch": "02",
            "oee_pct": 65.5,
            "appointment_count": 4,
        },
    ]

    use_case = GetProductionOeeSeriesUseCase(repository)
    result = use_case.execute(
        ProductionOeeSeriesRequest(
            granularity="month",
            date_start="2026-05-01",
            date_end="2026-05-31",
            branch="02",
        )
    )

    assert result.branch == "02"
    assert result.points[0].oee_filial_01 is None
    assert result.points[0].oee_filial_02 == 65.5

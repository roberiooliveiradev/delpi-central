"""Use case — série de OPs finalizadas (C2_DATRF)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.production_appointments.finished_ops_series_query_request import (
    FinishedOpsSeriesQueryRequest,
)
from app.application.use_cases.production_appointments.production_appointments_use_cases import (
    GetProductionAppointmentsFinishedOpsSeriesUseCase,
    _bucket_to_periodo,
)


def test_bucket_to_periodo_day_and_month() -> None:
    assert _bucket_to_periodo("20260615", "day") == "2026-06-15"
    assert _bucket_to_periodo("202606", "month") == "2026-06"
    assert _bucket_to_periodo("", "day") == ""


def test_finished_ops_series_use_case_maps_points_and_totals() -> None:
    repo = MagicMock()
    repo.get_finished_ops_series.return_value = [
        {"bucket": "20260601", "ops_finished_count": 3},
        {"bucket": "20260602", "ops_finished_count": 5},
    ]
    use_case = GetProductionAppointmentsFinishedOpsSeriesUseCase(repo)
    request = FinishedOpsSeriesQueryRequest.from_query(
        branch="01",
        date_start="2026-06-01",
        date_end="2026-06-30",
        mother_op=True,
        granularity="day",
    )

    result = use_case.execute(request)

    repo.get_finished_ops_series.assert_called_once()
    call_kwargs = repo.get_finished_ops_series.call_args.kwargs
    assert call_kwargs["branch"] == "01"
    assert call_kwargs["mother_op"] is True
    assert call_kwargs["granularity"] == "day"
    assert call_kwargs["date_start"] == "20260601"
    assert call_kwargs["date_end_exclusive"] == "20260701"
    assert result["totals"]["ops_finished_count"] == 8
    assert result["points"][0] == {
        "bucket": "20260601",
        "periodo": "2026-06-01",
        "ops_finished_count": 3,
    }
    assert result["filters"]["mother_op"] is True

"""Use case — série temporal de apontamentos (ISO periodo)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.production_appointments.production_appointments_query_request import (
    ProductionAppointmentsQueryRequest,
)
from app.application.use_cases.production_appointments.production_appointments_use_cases import (
    GetProductionAppointmentsSeriesUseCase,
)


def test_series_use_case_maps_appointment_date_to_iso_periodo() -> None:
    repo = MagicMock()
    repo.get_series.return_value = [
        {
            "appointment_date": "20260701",
            "appointment_count": 12,
            "qty_produced": 100.0,
            "qty_lost": 1.0,
        },
        {
            "appointment_date": "20260715",
            "appointment_count": 8,
            "qty_produced": 50.0,
            "qty_lost": 0.0,
        },
    ]
    use_case = GetProductionAppointmentsSeriesUseCase(repo)
    request = ProductionAppointmentsQueryRequest.from_query(
        branch="01",
        date_start="2026-07-01",
        date_end="2026-07-31",
        granularity="day",
    )

    result = use_case.execute(request)

    assert result["granularity"] == "day"
    assert result["points"][0]["bucket"] == "20260701"
    assert result["points"][0]["periodo"] == "2026-07-01"
    assert result["points"][0]["appointment_date"] == "2026-07-01"
    assert result["points"][1]["periodo"] == "2026-07-15"


def test_series_use_case_month_granularity_iso_yyyy_mm() -> None:
    repo = MagicMock()
    repo.get_series.return_value = [
        {
            "appointment_date": "202607",
            "appointment_count": 100,
            "qty_produced": 1000.0,
            "qty_lost": 10.0,
        },
    ]
    use_case = GetProductionAppointmentsSeriesUseCase(repo)
    request = ProductionAppointmentsQueryRequest.from_query(
        branch="01",
        date_start="2026-01-01",
        date_end="2026-07-31",
        granularity="month",
    )

    result = use_case.execute(request)

    assert result["points"][0]["bucket"] == "202607"
    assert result["points"][0]["periodo"] == "2026-07"
    assert result["points"][0]["appointment_date"] == "2026-07"

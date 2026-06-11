import pytest

from app.domain.services.production.production_loss_type_filter_service import (
    ProductionLossTypeFilterService,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


def test_resolve_closed_open_period_defaults_to_current_month() -> None:
    start, end = ProtheusDateRangeService.resolve_closed_open_period()
    assert len(start) == 8
    assert len(end) == 8
    assert start.endswith("01")
    assert start[:6] == end[:6] or int(end[4:6]) == int(start[4:6]) + 1


def test_resolve_closed_open_period_with_explicit_dates() -> None:
    start, end = ProtheusDateRangeService.resolve_closed_open_period(
        date_start="2026-03-01",
        date_end="2026-03-31",
    )
    assert start == "20260301"
    assert end == "20260401"


def test_resolve_reference_date_accepts_iso() -> None:
    assert ProtheusDateRangeService.resolve_reference_date("2026-06-11") == "20260611"


def test_resolve_reference_date_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        ProtheusDateRangeService.resolve_closed_open_period(date_start="invalid")


def test_loss_type_filter_maps_refugo() -> None:
    clause, params = ProductionLossTypeFilterService.sql_in_clause("refugo")
    assert "IN (?)" in clause
    assert params == ["R"]


def test_loss_type_filter_maps_both() -> None:
    clause, params = ProductionLossTypeFilterService.sql_in_clause("both")
    assert params == ["R", "S"]

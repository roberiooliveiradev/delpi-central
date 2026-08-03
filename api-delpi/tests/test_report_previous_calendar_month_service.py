"""Unit — períodos mês anterior / comparativo do Relatório Gerencial."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.domain.services.reports.report_previous_calendar_month_service import (
    ReportPreviousCalendarMonthService,
)


def test_resolve_mid_month() -> None:
    pair = ReportPreviousCalendarMonthService.resolve(date(2026, 7, 31))
    assert pair.report.start_date == "2026-06-01"
    assert pair.report.end_date == "2026-06-30"
    assert pair.report.label_pt == "jun/2026"
    assert pair.compare.start_date == "2026-05-01"
    assert pair.compare.end_date == "2026-05-31"
    assert pair.compare.label_pt == "mai/2026"


def test_resolve_year_boundary() -> None:
    pair = ReportPreviousCalendarMonthService.resolve(date(2026, 1, 1))
    assert pair.report.start_date == "2025-12-01"
    assert pair.report.end_date == "2025-12-31"
    assert pair.compare.start_date == "2025-11-01"
    assert pair.compare.end_date == "2025-11-30"


def test_resolve_february_leap() -> None:
    pair = ReportPreviousCalendarMonthService.resolve(date(2024, 3, 15))
    assert pair.report.start_date == "2024-02-01"
    assert pair.report.end_date == "2024-02-29"
    assert pair.compare.start_date == "2024-01-01"
    assert pair.compare.end_date == "2024-01-31"


def test_resolve_february_non_leap() -> None:
    pair = ReportPreviousCalendarMonthService.resolve(date(2025, 3, 1))
    assert pair.report.end_date == "2025-02-28"


def test_resolve_datetime_timezone() -> None:
    tz = ZoneInfo("America/Sao_Paulo")
    # 2026-08-01 02:00 UTC = ainda 31/jul em SP → mês relatório = junho
    as_of = datetime(2026, 8, 1, 2, 0, tzinfo=ZoneInfo("UTC"))
    pair = ReportPreviousCalendarMonthService.resolve(
        as_of,
        timezone_name="America/Sao_Paulo",
    )
    # 02:00 UTC = 23:00 31/jul SP → report = junho
    local = as_of.astimezone(tz).date()
    expected = ReportPreviousCalendarMonthService.resolve(local)
    assert pair.report.start_date == expected.report.start_date

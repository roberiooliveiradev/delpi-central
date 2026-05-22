from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_period_date,
)


def test_normalize_si_period_date_from_iso() -> None:
    assert normalize_si_period_date("2026-05-22") == "22-05-2026"


def test_normalize_si_period_date_keeps_delpi_format() -> None:
    assert normalize_si_period_date("22-05-2026") == "22-05-2026"

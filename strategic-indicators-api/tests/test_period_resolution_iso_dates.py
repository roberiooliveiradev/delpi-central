from datetime import date

from si_app.application.services.strategic_indicators.period_resolution import (
    clamp_resolved_period_to_elapsed,
    normalize_dashboard_period_date,
    period_extends_beyond_today,
    resolve_period,
    stored_period_matches_request,
)


def test_normalize_dashboard_period_date_from_iso() -> None:
    assert normalize_dashboard_period_date("2026-05-01") == "01-05-2026"


def test_resolve_period_competence_from_iso_dates() -> None:
    period = resolve_period(
        competence=None,
        start_date="2026-05-01",
        end_date="2026-05-22",
    )

    assert period.competence == "2026-05"
    assert period.start_date == "01-05-2026"
    assert period.end_date == "22-05-2026"


def test_clamp_resolved_period_to_elapsed_limits_end_to_today() -> None:
    period = resolve_period(
        competence="2026-07",
        start_date="01-07-2026",
        end_date="31-07-2026",
    )
    clamped, entirely_future = clamp_resolved_period_to_elapsed(
        period,
        today=date(2026, 7, 7),
    )

    assert entirely_future is False
    assert clamped.start_date == "01-07-2026"
    assert clamped.end_date == "07-07-2026"


def test_clamp_resolved_period_marks_entirely_future_month() -> None:
    period = resolve_period(
        competence="2026-08",
        start_date="01-08-2026",
        end_date="31-08-2026",
    )
    _clamped, entirely_future = clamp_resolved_period_to_elapsed(
        period,
        today=date(2026, 7, 7),
    )

    assert entirely_future is True


def test_period_extends_beyond_today() -> None:
    period = resolve_period(
        competence="2026-08",
        start_date="01-08-2026",
        end_date="31-08-2026",
    )

    assert period_extends_beyond_today(period, today=date(2026, 7, 7)) is True
    assert period_extends_beyond_today(period, today=date(2026, 8, 31)) is False


def test_stored_period_matches_request() -> None:
    requested = resolve_period(
        competence="2026-07",
        start_date="01-07-2026",
        end_date="07-07-2026",
    )
    stored = resolve_period(
        competence="2026-07",
        start_date="01-07-2026",
        end_date="31-07-2026",
    )

    assert stored_period_matches_request(requested, requested) is True
    assert stored_period_matches_request(requested, stored) is False

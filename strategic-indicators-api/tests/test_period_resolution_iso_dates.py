from si_app.application.services.strategic_indicators.period_resolution import (
    normalize_dashboard_period_date,
    resolve_period,
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

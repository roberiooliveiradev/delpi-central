from __future__ import annotations

from si_app.application.services.strategic_indicators.period_snapshot_versions import (
    resolve_period_scores_serve,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    resolve_period,
)


def _entry(*, version: int, is_clean: bool, igd: float, errors: list | None = None):
    period = resolve_period(competence="2026-05", start_date=None, end_date=None)
    snapshot = StrategicIndicatorsPeriodSnapshot(
        period=period,
        measurements=[],
        measurement_errors=errors or [],
        calculated_indicators=[],
        calculated_departments=[],
        igd=igd,
        igd_exact=igd,
        classification="stable",
    )
    return PeriodScoresCacheEntry(
        snapshot=snapshot,
        catalog_inputs_hash="hash",
        version_number=version,
        is_clean=is_clean,
    )


def test_resolve_period_scores_serves_latest_clean() -> None:
    entries = [
        _entry(version=1, is_clean=True, igd=7.5),
        _entry(
            version=2,
            is_clean=False,
            igd=0.0,
            errors=[{"department_id": "hr", "message": "timeout", "source": "x"}],
        ),
    ]

    resolved = resolve_period_scores_serve(entries)
    assert resolved is not None
    assert resolved.version_number == 1
    assert resolved.snapshot.igd == 7.5
    assert len(resolved.snapshot.measurement_errors) == 1

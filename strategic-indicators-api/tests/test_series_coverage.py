from si_app.application.services.strategic_indicators.series_coverage import (
    build_series_coverage,
)


def test_build_series_coverage_lists_missing() -> None:
    coverage = build_series_coverage(
        months_requested=6,
        competences_requested=["2026-01", "2026-02", "2026-03"],
        competences_returned=["2026-02", "2026-03"],
    )
    assert coverage["missing_competences"] == ["2026-01"]
    assert coverage["months_requested"] == 6

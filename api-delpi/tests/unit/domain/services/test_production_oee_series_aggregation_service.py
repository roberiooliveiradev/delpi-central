from app.domain.services.production.production_oee_series_aggregation_service import (
    resolve_bucket_oee_pct,
    resolve_period_oee_by_branch,
)


def test_resolve_bucket_oee_pct_weighted_average() -> None:
    daily_rows = [
        {
            "production_date": "2026-06-01",
            "branch": "01",
            "oee_pct": 80.0,
            "appointment_count": 10,
        },
        {
            "production_date": "2026-06-02",
            "branch": "01",
            "oee_pct": 60.0,
            "appointment_count": 10,
        },
    ]

    result = resolve_bucket_oee_pct(
        daily_rows,
        branch="01",
        date_start="2026-06-01",
        date_end="2026-06-02",
    )

    assert result == 70.0


def test_resolve_bucket_oee_pct_returns_none_without_rows() -> None:
    assert (
        resolve_bucket_oee_pct(
            [],
            branch="01",
            date_start="2026-06-01",
            date_end="2026-06-02",
        )
        is None
    )


def test_resolve_period_oee_by_branch_matches_round_avg_over_period() -> None:
    # Componentes brutos por dia/filial: derivar deve equivaler a
    # ROUND(AVG(EFICIENCIA_PERCENTUAL), 2) por filial no período inteiro.
    daily_rows = [
        {
            "branch": "01",
            "efficiency_sum": 250.0,  # ex.: 80 + 90 + 80
            "efficiency_sample_count": 3,
        },
        {
            "branch": "01",
            "efficiency_sum": 100.0,  # ex.: 100
            "efficiency_sample_count": 1,
        },
        {
            "branch": "02",
            "efficiency_sum": 130.0,  # ex.: 65 + 65
            "efficiency_sample_count": 2,
        },
    ]

    result = resolve_period_oee_by_branch(daily_rows)

    assert result == [
        {"branch": "01", "oee_pct": round((250.0 + 100.0) / 4, 2)},
        {"branch": "02", "oee_pct": 65.0},
    ]


def test_resolve_period_oee_by_branch_handles_missing_samples() -> None:
    daily_rows = [
        {"branch": "01", "efficiency_sum": 0.0, "efficiency_sample_count": 0},
        {"branch": "", "efficiency_sum": 99.0, "efficiency_sample_count": 1},
    ]

    result = resolve_period_oee_by_branch(daily_rows)

    assert result == [{"branch": "01", "oee_pct": None}]


def test_resolve_period_oee_by_branch_empty() -> None:
    assert resolve_period_oee_by_branch([]) == []

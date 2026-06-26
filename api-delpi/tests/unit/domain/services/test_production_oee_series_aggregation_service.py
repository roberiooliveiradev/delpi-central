from app.domain.services.production.production_oee_series_aggregation_service import (
    resolve_bucket_oee_pct,
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

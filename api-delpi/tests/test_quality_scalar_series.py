"""Unit tests for quality scalar series use case + operationId coverage."""

from __future__ import annotations

from app.application.use_cases.quality.get_quality_scalar_series_use_case import (
    GetQualityScalarSeriesUseCase,
    iter_month_buckets,
)


def test_iter_month_buckets_delpi_dates() -> None:
    buckets, truncated = iter_month_buckets(
        start_date="01-01-2026",
        end_date="28-02-2026",
    )
    assert truncated is False
    assert [key for key, _, _ in buckets] == ["2026-01", "2026-02"]


def test_quality_scalar_series_use_case_calls_fetch_per_month() -> None:
    calls: list[tuple[str | None, str, str]] = []

    def fetch(branch, start, end):
        calls.append((branch, start, end))
        return {"scrap_cost_pct": 1.5}

    result = GetQualityScalarSeriesUseCase(
        metric="scrap_cost_pct",
        fetch_metrics=fetch,
    ).execute(
        branch="01",
        date_start="01-01-2026",
        date_end="28-02-2026",
    )
    assert len(result.points) == 2
    assert len(calls) == 2
    assert result.points[0].metrics["scrap_cost_pct"] == 1.5


def test_quality_series_operation_ids_registered() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    for oid in (
        "get_quality_scrap_cost_pct_series",
        "get_quality_rework_cost_pct_series",
        "get_kaizen_summary_series",
        "get_audit_5s_summary_series",
    ):
        assert oid in ROUTE_CONTRACTS, oid

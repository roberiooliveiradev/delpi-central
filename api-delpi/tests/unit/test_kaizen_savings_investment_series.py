"""Testes da série ganhos financeiros vs investimento (Kaizômetro)."""

from datetime import date
from decimal import Decimal

import pytest

from app.domain.services.kaizen.kaizen_savings_investment_series import (
    build_savings_investment_series,
)


def _row(**overrides) -> dict:
    base = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "branch_code": "01",
        "title": "Kaizen teste",
        "investment": Decimal("100"),
        "daily_savings": Decimal("10"),
        "status": "implantado",
        "date_committee_approved": None,
        "date_implemented": date(2026, 7, 10),
    }
    base.update(overrides)
    return base


def test_month_series_savings_and_investment_align_with_summary_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return date(2026, 7, 20)

    monkeypatch.setattr(
        "app.domain.services.kaizen.kaizen_savings_validity.date",
        _FixedDate,
    )

    result = build_savings_investment_series(
        [_row()],
        granularity="month",
        date_start="2026-07-01",
        date_end="2026-07-31",
        today=date(2026, 7, 20),
    )

    assert result["granularity"] == "month"
    assert result["total"] == 1
    assert result["points"][0]["periodo"] == "2026-07"
    # 10/07..20/07 = 11 dias × R$ 10
    assert result["points"][0]["savings"] == pytest.approx(110.0)
    assert result["points"][0]["investment"] == pytest.approx(100.0)
    assert result["total_savings"] == pytest.approx(110.0)
    assert result["total_investment"] == pytest.approx(100.0)


def test_day_series_allocates_investment_on_anchor_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return date(2026, 7, 12)

    monkeypatch.setattr(
        "app.domain.services.kaizen.kaizen_savings_validity.date",
        _FixedDate,
    )

    result = build_savings_investment_series(
        [
            _row(
                date_committee_approved=date(2026, 7, 11),
                date_implemented=date(2026, 7, 10),
                investment=Decimal("50"),
                daily_savings=Decimal("5"),
            )
        ],
        granularity="day",
        date_start="2026-07-10",
        date_end="2026-07-12",
        today=date(2026, 7, 12),
    )

    by_period = {point["periodo"]: point for point in result["points"]}
    assert by_period["2026-07-10"]["investment"] == 0.0
    assert by_period["2026-07-11"]["investment"] == pytest.approx(50.0)
    assert by_period["2026-07-10"]["savings"] == pytest.approx(5.0)
    assert by_period["2026-07-11"]["savings"] == pytest.approx(5.0)
    assert by_period["2026-07-12"]["savings"] == pytest.approx(5.0)


def test_aprovado_counts_investment_not_savings() -> None:
    result = build_savings_investment_series(
        [
            _row(
                status="aprovado",
                date_committee_approved=date(2026, 7, 5),
                date_implemented=None,
                daily_savings=Decimal("99"),
                investment=Decimal("40"),
            )
        ],
        granularity="month",
        date_start="2026-07-01",
        date_end="2026-07-31",
        today=date(2026, 7, 20),
    )

    assert result["points"][0]["savings"] == 0.0
    assert result["points"][0]["investment"] == pytest.approx(40.0)

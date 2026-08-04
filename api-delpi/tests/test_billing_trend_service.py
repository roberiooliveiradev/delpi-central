from __future__ import annotations

from app.domain.services.pedidos_venda_abertos.billing_trend_service import (
    BILLING_TREND_DEADBAND_PCT,
    resolve_billing_trend,
)


def test_billing_trend_insufficient_when_both_zero() -> None:
    result = resolve_billing_trend(billed_recent_6m=0, billed_prior_6m=0)
    assert result.direction == "insufficient"
    assert result.change_pct is None


def test_billing_trend_up_when_prior_zero_and_recent_positive() -> None:
    result = resolve_billing_trend(billed_recent_6m=1000, billed_prior_6m=0)
    assert result.direction == "up"
    assert result.change_pct is None


def test_billing_trend_up_above_deadband() -> None:
    result = resolve_billing_trend(billed_recent_6m=110, billed_prior_6m=100)
    assert result.direction == "up"
    assert result.change_pct is not None
    assert abs(result.change_pct - 10.0) < 1e-9


def test_billing_trend_down_below_deadband() -> None:
    result = resolve_billing_trend(billed_recent_6m=90, billed_prior_6m=100)
    assert result.direction == "down"
    assert result.change_pct is not None
    assert abs(result.change_pct - (-10.0)) < 1e-9


def test_billing_trend_stable_inside_deadband() -> None:
    result = resolve_billing_trend(billed_recent_6m=104, billed_prior_6m=100)
    assert result.direction == "stable"
    assert result.change_pct is not None
    assert abs(result.change_pct - 4.0) < 1e-9
    assert abs(result.change_pct) <= BILLING_TREND_DEADBAND_PCT


def test_billing_trend_stable_at_exact_deadband() -> None:
    result = resolve_billing_trend(billed_recent_6m=105, billed_prior_6m=100)
    assert result.direction == "stable"
    assert result.change_pct is not None
    assert abs(result.change_pct - 5.0) < 1e-9

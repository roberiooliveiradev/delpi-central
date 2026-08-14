"""Tendência de faturamento — janela recente vs. anterior (carteira B2B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BillingTrendDirection = Literal["up", "down", "stable", "insufficient"]

# Faixa morta (±%) para ignorar oscilação pequena — padrão comum em health score CRM.
BILLING_TREND_DEADBAND_PCT = 5.0

DEFAULT_BILLING_TREND_WINDOW_DAYS = 30
MIN_BILLING_TREND_WINDOW_DAYS = 1
MAX_BILLING_TREND_WINDOW_DAYS = 365
BILLING_TREND_WINDOW_PRESETS = frozenset({7, 30, 90})


def clamp_billing_trend_window_days(value: int | None) -> int:
    """Presets 7/30/90 ou custom 1–365; default 30."""
    if value is None:
        return DEFAULT_BILLING_TREND_WINDOW_DAYS
    try:
        days = int(value)
    except (TypeError, ValueError):
        return DEFAULT_BILLING_TREND_WINDOW_DAYS
    if days in BILLING_TREND_WINDOW_PRESETS:
        return days
    return max(MIN_BILLING_TREND_WINDOW_DAYS, min(MAX_BILLING_TREND_WINDOW_DAYS, days))


@dataclass(frozen=True, slots=True)
class BillingTrendResult:
    direction: BillingTrendDirection
    change_pct: float | None


def resolve_billing_trend(
    *,
    billed_recent_6m: float | None = None,
    billed_prior_6m: float | None = None,
    billed_recent: float | None = None,
    billed_prior: float | None = None,
    deadband_pct: float = BILLING_TREND_DEADBAND_PCT,
) -> BillingTrendResult:
    """
    Compara a janela recente com a janela anterior de mesma duração.

    - insufficient: ambos ≈ 0
    - up: prior = 0 e recent > 0, ou variação > +deadband
    - down: variação < −deadband
    - stable: |variação| ≤ deadband

    Aceita aliases `billed_recent`/`billed_prior` (preferidos) ou
    `billed_recent_6m`/`billed_prior_6m` (legado).
    """
    recent_raw = billed_recent if billed_recent is not None else billed_recent_6m
    prior_raw = billed_prior if billed_prior is not None else billed_prior_6m
    recent = max(0.0, float(recent_raw or 0.0))
    prior = max(0.0, float(prior_raw or 0.0))

    if prior <= 0.0 and recent <= 0.0:
        return BillingTrendResult(direction="insufficient", change_pct=None)

    if prior <= 0.0:
        return BillingTrendResult(direction="up", change_pct=None)

    pct = ((recent - prior) / prior) * 100.0
    if pct > deadband_pct:
        return BillingTrendResult(direction="up", change_pct=pct)
    if pct < -deadband_pct:
        return BillingTrendResult(direction="down", change_pct=pct)
    return BillingTrendResult(direction="stable", change_pct=pct)

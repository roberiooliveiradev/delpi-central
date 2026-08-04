"""Tendência de faturamento — semestre recente vs. anterior (carteira B2B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BillingTrendDirection = Literal["up", "down", "stable", "insufficient"]

# Faixa morta (±%) para ignorar oscilação pequena — padrão comum em health score CRM.
BILLING_TREND_DEADBAND_PCT = 5.0


@dataclass(frozen=True, slots=True)
class BillingTrendResult:
    direction: BillingTrendDirection
    change_pct: float | None


def resolve_billing_trend(
    *,
    billed_recent_6m: float,
    billed_prior_6m: float,
    deadband_pct: float = BILLING_TREND_DEADBAND_PCT,
) -> BillingTrendResult:
    """
    Compara os últimos ~6 meses com os 6 anteriores na janela móvel de 12 meses.

    - insufficient: ambos ≈ 0
    - up: prior = 0 e recent > 0, ou variação > +deadband
    - down: variação < −deadband
    - stable: |variação| ≤ deadband
    """
    recent = max(0.0, float(billed_recent_6m or 0.0))
    prior = max(0.0, float(billed_prior_6m or 0.0))

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

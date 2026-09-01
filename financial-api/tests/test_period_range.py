from __future__ import annotations

from datetime import date

import pytest

from financial_app.domain.errors import InvalidPeriod
from financial_app.domain.services.period_range import (
    current_month_bounds,
    resolve_inclusive_period_or_default,
)


def test_current_month_bounds() -> None:
    assert current_month_bounds(date(2026, 9, 15)) == ("2026-09-01", "2026-09-15")


def test_resolve_inclusive_period_or_default_uses_current_month() -> None:
    assert resolve_inclusive_period_or_default(None, None, today=date(2026, 9, 1)) == (
        "2026-09-01",
        "2026-09-01",
    )


def test_resolve_inclusive_period_or_default_keeps_explicit_range() -> None:
    assert resolve_inclusive_period_or_default("2026-07-01", "2026-07-31") == (
        "2026-07-01",
        "2026-07-31",
    )


def test_resolve_inclusive_period_or_default_rejects_partial_range() -> None:
    with pytest.raises(InvalidPeriod):
        resolve_inclusive_period_or_default("2026-07-01", None)

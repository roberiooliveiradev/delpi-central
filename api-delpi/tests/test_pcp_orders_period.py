"""Testes — recorte de entrega das OPs PCP."""

from __future__ import annotations

from datetime import date

import pytest

from app.application.dto.production.pcp_orders_request import PcpOrdersPeriod


def test_unbounded_delivery_skips_default_twelve_month_window() -> None:
    period = PcpOrdersPeriod.resolve(branch="01", unbounded_delivery=True)
    assert period.unbounded_delivery is True
    assert period.delivery_start is None
    assert period.delivery_end is None
    kwargs = period.filter_kwargs()
    assert kwargs["unbounded_delivery"] is True
    assert kwargs["delivery_start"] is None
    assert kwargs["delivery_end"] is None


def test_unbounded_delivery_keeps_explicit_dates_without_max_window() -> None:
    period = PcpOrdersPeriod.resolve(
        branch="02",
        delivery_start="2003-11-03",
        delivery_end="2040-06-15",
        unbounded_delivery=True,
    )
    assert period.delivery_start == date(2003, 11, 3)
    assert period.delivery_end == date(2040, 6, 15)
    assert period.unbounded_delivery is True


def test_bounded_delivery_still_rejects_window_over_24_months() -> None:
    with pytest.raises(ValueError, match="Período máximo permitido"):
        PcpOrdersPeriod.resolve(
            branch="01",
            delivery_start="2020-01-01",
            delivery_end="2026-01-01",
            unbounded_delivery=False,
        )


def test_default_period_is_bounded() -> None:
    period = PcpOrdersPeriod.resolve(branch="01")
    assert period.unbounded_delivery is False
    assert period.delivery_start is not None
    assert period.delivery_end is not None
    assert period.delivery_end == date.today()

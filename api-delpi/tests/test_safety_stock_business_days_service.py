from __future__ import annotations

from datetime import date

from app.domain.services.supplies.safety_stock_business_days_service import (
    SafetyStockBusinessDaysService,
)


def test_count_inclusive_skips_weekends() -> None:
    # Sexta 2026-07-17 a segunda 2026-07-20 → sex, seg = 2
    assert (
        SafetyStockBusinessDaysService.count_inclusive(
            date(2026, 7, 17),
            date(2026, 7, 20),
        )
        == 2
    )


def test_count_in_calendar_span_for_lead_time() -> None:
    # 7 dias corridos a partir de sexta incluem só 5 úteis
    assert (
        SafetyStockBusinessDaysService.count_in_calendar_span(
            7,
            start=date(2026, 7, 17),
        )
        == 5
    )


def test_zero_calendar_days_returns_zero() -> None:
    assert SafetyStockBusinessDaysService.count_in_calendar_span(0) == 0
    assert SafetyStockBusinessDaysService.count_inclusive(
        date(2026, 7, 20),
        date(2026, 7, 17),
    ) == 0

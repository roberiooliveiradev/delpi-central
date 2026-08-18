"""Availability = postponed vs available using delivery-horizon buckets."""

from __future__ import annotations

from datetime import date

from commercial_app.domain.services.open_order_availability_classification_service import (
    AVAILABILITY_AVAILABLE,
    AVAILABILITY_POSTPONED,
    AVAILABILITY_UNDATED,
    OpenOrderAvailabilityClassificationService,
)

AS_OF = date(2026, 8, 18)


def test_future_delivery_is_postponed() -> None:
    svc = OpenOrderAvailabilityClassificationService()
    assert (
        svc.classify({"data_entrega": "2026-10-01", "saldo": 1}, as_of=AS_OF)
        == AVAILABILITY_POSTPONED
    )


def test_current_month_and_overdue_are_available() -> None:
    svc = OpenOrderAvailabilityClassificationService()
    assert (
        svc.classify({"data_entrega": "2026-08-20", "saldo": 1}, as_of=AS_OF)
        == AVAILABILITY_AVAILABLE
    )
    assert (
        svc.classify({"data_entrega": "2026-08-01", "saldo": 1}, as_of=AS_OF)
        == AVAILABILITY_AVAILABLE
    )


def test_missing_delivery_is_undated() -> None:
    svc = OpenOrderAvailabilityClassificationService()
    assert svc.classify({"data_entrega": None}, as_of=AS_OF) == AVAILABILITY_UNDATED


def test_enrich_writes_availability_field() -> None:
    item = OpenOrderAvailabilityClassificationService().enrich_item(
        {"pedido": "1", "data_entrega": "2026-12-01"},
        as_of=AS_OF,
    )
    assert item["availability"] == AVAILABILITY_POSTPONED
    assert item["pedido"] == "1"

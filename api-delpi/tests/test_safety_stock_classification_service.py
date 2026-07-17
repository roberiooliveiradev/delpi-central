from __future__ import annotations

import pytest

from app.domain.services.supplies.safety_stock_classification_service import (
    STATUS_ABOVE,
    STATUS_AT,
    STATUS_BELOW,
    STATUS_WITHOUT,
    calculate_deficit_quantity,
    classify_safety_stock_status,
)


@pytest.mark.parametrize(
    ("safety_stock", "available_stock", "expected"),
    [
        (None, 10, STATUS_WITHOUT),
        (0, 10, STATUS_WITHOUT),
        (-1, 10, STATUS_WITHOUT),
        (100, 50, STATUS_BELOW),
        (100, 99.99995, STATUS_AT),
        (100, 100, STATUS_AT),
        (100, 100.00005, STATUS_AT),
        (100, 150, STATUS_ABOVE),
    ],
)
def test_classify_safety_stock_status(safety_stock, available_stock, expected) -> None:
    assert (
        classify_safety_stock_status(
            safety_stock=safety_stock,
            available_stock=available_stock,
        )
        == expected
    )


def test_deficit_quantity_never_negative() -> None:
    assert calculate_deficit_quantity(safety_stock=100, available_stock=150) == 0.0
    assert calculate_deficit_quantity(safety_stock=0, available_stock=0) == 0.0


def test_deficit_quantity_when_below() -> None:
    assert calculate_deficit_quantity(safety_stock=100, available_stock=40) == 60.0


def test_deficit_uses_available_balance_not_only_primary() -> None:
    # ESTSEG 100; arm.01=50; saldo disponível 50+20+10=80 → déficit 20
    assert calculate_deficit_quantity(safety_stock=100, available_stock=80) == 20.0
    assert classify_safety_stock_status(safety_stock=100, available_stock=80) == STATUS_BELOW


def test_primary_stock_legacy_parameter_still_supported() -> None:
    assert classify_safety_stock_status(safety_stock=100, available_stock=None, primary_stock=50) == (
        STATUS_BELOW
    )

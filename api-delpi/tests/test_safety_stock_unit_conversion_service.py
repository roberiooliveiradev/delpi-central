from __future__ import annotations

from app.domain.services.supplies.safety_stock_unit_conversion_service import (
    convert_quantity_to_primary_unit,
)


def test_same_unit_is_identity() -> None:
    result = convert_quantity_to_primary_unit(
        quantity=10,
        source_unit="PC",
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12,
        conversion_type="M",
    )
    assert result.compatible is True
    assert result.quantity == 10


def test_secondary_unit_multiply_converts_to_primary() -> None:
    # 1 PC = 1000 MM → 2000 MM = 2 PC
    result = convert_quantity_to_primary_unit(
        quantity=2000,
        source_unit="MM",
        primary_unit="PC",
        secondary_unit="MM",
        conversion_factor=1000,
        conversion_type="M",
    )
    assert result.compatible is True
    assert result.quantity == 2.0


def test_secondary_unit_divide_converts_to_primary() -> None:
    # TIPCONV=D: qty_segum = qty_um / factor → qty_um = qty_segum * factor
    result = convert_quantity_to_primary_unit(
        quantity=2,
        source_unit="CX",
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12,
        conversion_type="D",
    )
    assert result.compatible is True
    assert result.quantity == 24.0


def test_incompatible_unit_rejected() -> None:
    result = convert_quantity_to_primary_unit(
        quantity=10,
        source_unit="KG",
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12,
        conversion_type="M",
    )
    assert result.compatible is False
    assert result.quantity is None
    assert result.reason == "incompatible_unit"

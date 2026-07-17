"""Conversão de unidade Protheus (B1_UM × B1_SEGUM × B1_CONV × B1_TIPCONV)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UnitConversionResult:
    quantity: float | None
    compatible: bool
    reason: str | None = None


def _normalize_unit(value: str | None) -> str:
    return str(value or "").strip().upper()


def _parse_positive_factor(raw: float | int | str | None) -> float | None:
    try:
        value = float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None
    if value is None or value <= 0:
        return None
    return value


def convert_quantity_to_primary_unit(
    *,
    quantity: float | int | None,
    source_unit: str | None,
    primary_unit: str | None,
    secondary_unit: str | None,
    conversion_factor: float | int | str | None,
    conversion_type: str | None,
) -> UnitConversionResult:
    """Converte quantidade da unidade de origem para a unidade primária (B1_UM)."""
    try:
        qty = float(quantity or 0)
    except (TypeError, ValueError):
        return UnitConversionResult(None, False, "invalid_quantity")

    source = _normalize_unit(source_unit)
    primary = _normalize_unit(primary_unit)
    secondary = _normalize_unit(secondary_unit)

    if not source or not primary:
        return UnitConversionResult(None, False, "missing_unit")

    if source == primary:
        return UnitConversionResult(qty, True)

    if not secondary or source != secondary:
        return UnitConversionResult(None, False, "incompatible_unit")

    factor = _parse_positive_factor(conversion_factor)
    tip = _normalize_unit(conversion_type)
    if factor is None or tip not in {"M", "D"}:
        return UnitConversionResult(None, False, "missing_conversion")

    # TIPCONV=M: 1 UM = CONV SEGUM → qty_um = qty_segum / CONV
    # TIPCONV=D: 1 UM = 1/CONV SEGUM → qty_um = qty_segum * CONV
    if tip == "M":
        return UnitConversionResult(qty / factor, True)
    return UnitConversionResult(qty * factor, True)

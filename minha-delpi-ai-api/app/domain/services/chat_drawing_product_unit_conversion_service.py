"""Conversão Protheus SB1010 (B1_UM, B1_SEGUM, B1_CONV, B1_TIPCONV) para análise de desenho."""

from __future__ import annotations

from typing import Any


class ChatDrawingProductUnitConversionService:
    @classmethod
    def apply_conversion_factor(
        cls,
        quantity: float,
        conversion_factor: float | None,
        conversion_type: str | None,
    ) -> float | None:
        factor = cls._parse_positive(conversion_factor)

        if factor is None:
            return None

        normalized_type = str(conversion_type or "M").strip().upper()

        if normalized_type == "D":
            return quantity / factor

        return quantity * factor

    @classmethod
    def quantity_to_mm(
        cls,
        quantity: float,
        unit: str,
        *,
        secondary_unit: str | None = None,
        conversion_factor: float | None = None,
        conversion_type: str | None = None,
    ) -> float | None:
        normalized_unit = str(unit or "").strip().upper()

        if not normalized_unit:
            return None

        physical_mm = cls._physical_quantity_to_mm(quantity, normalized_unit)

        if physical_mm is not None:
            return physical_mm

        secondary = str(secondary_unit or "").strip().upper()
        converted = cls.apply_conversion_factor(
            quantity,
            conversion_factor,
            conversion_type,
        )

        if converted is None or not secondary:
            return None

        return cls._physical_quantity_to_mm(converted, secondary)

    @classmethod
    def quantity_to_mm_from_structure_item(
        cls,
        quantity: float,
        item: dict[str, Any],
    ) -> float | None:
        if not isinstance(item, dict):
            return None

        unit = cls._item_unit(item)

        return cls.quantity_to_mm(
            quantity,
            unit,
            secondary_unit=str(item.get("secondary_unit") or ""),
            conversion_factor=cls._parse_positive(item.get("conversion_factor")),
            conversion_type=str(item.get("conversion_type") or ""),
        )

    @classmethod
    def per_piece_mm(
        cls,
        *,
        quantity: float,
        unit: str,
        batch_scale: float,
        item: dict[str, Any] | None = None,
    ) -> float | None:
        if batch_scale <= 0:
            return None

        if isinstance(item, dict):
            total_mm = cls.quantity_to_mm_from_structure_item(quantity, item)
        else:
            total_mm = cls.quantity_to_mm(quantity, unit)

        if total_mm is None:
            return None

        return total_mm / batch_scale

    @classmethod
    def _physical_quantity_to_mm(cls, quantity: float, unit: str) -> float | None:
        if unit in {"MT", "M"}:
            return quantity * 1000.0

        if unit == "MM":
            return quantity

        return None

    @classmethod
    def _item_unit(cls, item: dict[str, Any]) -> str:
        for key in ("unit", "component_unit", "unidade"):
            raw = item.get(key)

            if raw is None:
                continue

            value = str(raw).strip().upper()

            if value:
                return value

        return ""

    @classmethod
    def _parse_positive(cls, raw: Any) -> float | None:
        if raw is None:
            return None

        try:
            value = float(str(raw).replace(",", ".").strip())
        except (TypeError, ValueError):
            return None

        return value if value > 0 else None

"""Formatação de quantidades do playbook — evita artefatos de float no JSON."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


class ProductPlaybookNumericService:
    DEFAULT_MAX_DECIMALS = 4

    QUANTITY_FIELD_NAMES = frozenset(
        {
            "quantity_required_for_one_pa",
            "available_quantity",
            "available_quantity_total",
            "current_quantity",
            "committed_quantity",
            "reserved_quantity",
            "pa_producible_from_stock",
            "pa_coverage_estimate",
            "max_pa_producible_from_stock_exact",
            "equivalent_in_pa",
            "percent_for_one_pa",
            "order_production_percent",
            "order_quantity",
            "reported_quantity",
            "produced_quantity_sc2",
            "shipped_quantity",
            "inspection_loss_quantity",
            "total_pa_reported_quantity",
            "total_pi_reported_quantity",
            "total_shipped_quantity",
            "total_inspection_loss_quantity",
            "accumulated_quantity",
        }
    )

    @classmethod
    def format_quantity(
        cls,
        value: object,
        *,
        max_decimals: int | None = None,
    ) -> str:
        if value in (None, ""):
            return "0"

        decimals = cls.DEFAULT_MAX_DECIMALS if max_decimals is None else max(0, int(max_decimals))

        try:
            if isinstance(value, Decimal):
                number = value
            elif isinstance(value, float):
                number = Decimal(str(value))
            elif isinstance(value, int):
                return str(value)
            else:
                text = str(value).strip().replace(",", ".")

                if not text:
                    return "0"

                number = Decimal(text)
        except (InvalidOperation, ValueError, TypeError):
            return str(value).strip() or "0"

        if decimals == 0:
            rounded = number.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        else:
            quantize_exp = Decimal("1").scaleb(-decimals)
            rounded = number.quantize(quantize_exp, rounding=ROUND_HALF_UP)

        normalized = rounded.normalize()
        formatted = format(normalized, "f")

        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")

        if formatted in ("", "-0"):
            return "0"

        return formatted

    @classmethod
    def to_float(cls, value: object) -> float:
        if value in (None, ""):
            return 0.0

        try:
            return float(cls.format_quantity(value))
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def normalize_row_quantities(cls, row: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(row, dict):
            return row

        normalized = dict(row)

        for field in cls.QUANTITY_FIELD_NAMES:
            if field not in normalized:
                continue

            normalized[field] = cls.format_quantity(normalized[field])

        return normalized

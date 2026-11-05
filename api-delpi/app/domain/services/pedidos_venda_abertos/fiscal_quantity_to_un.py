"""Normalização fiscal → UN para comparação com necessidades MyWEG.

Fatores canônicos alinhados à equivalência MyWEG / produção operacional:
1 MI = 1.000 UN. Sem float. Sem conversão inventada para KG/CX/MT.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

NORMALIZED_UNIT = "UN"
MI_TO_UN_FACTOR = Decimal("1000")

# Unidade fiscal → fator para UN (somente fatores comprovados).
_FACTOR_TO_UN: dict[str, Decimal] = {
    "UN": Decimal("1"),
    "UN.": Decimal("1"),
    "MI": MI_TO_UN_FACTOR,
}


@dataclass(frozen=True)
class FiscalQuantityToUnResult:
    original_quantity: Decimal | None
    original_unit: str
    quantity_un: Decimal | None
    normalized_unit: str | None
    conversion_factor: Decimal | None
    comparable: bool
    incompatibility_reason: str | None


def normalize_unit_code(value: Any) -> str:
    return str(value or "").strip().upper()


def parse_fiscal_quantity(value: Any) -> Decimal | None:
    """Parse estrito — quantidade inválida/ausente retorna None (não zero)."""
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def decimal_to_plain_str(value: Decimal) -> str:
    """String decimal sem notação científica e sem zeros à direita inúteis."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def convert_fiscal_quantity_to_un(
    *,
    quantity: Any,
    unit: Any,
) -> FiscalQuantityToUnResult:
    """Converte quantidade fiscal bruta para UN quando o fator for confiável."""
    original_unit = normalize_unit_code(unit)
    original_quantity = parse_fiscal_quantity(quantity)

    if original_quantity is None:
        return FiscalQuantityToUnResult(
            original_quantity=None,
            original_unit=original_unit,
            quantity_un=None,
            normalized_unit=None,
            conversion_factor=None,
            comparable=False,
            incompatibility_reason=(
                "Quantidade fiscal inválida ou ausente; não converter para zero."
            ),
        )

    if not original_unit:
        return FiscalQuantityToUnResult(
            original_quantity=original_quantity,
            original_unit="",
            quantity_un=None,
            normalized_unit=None,
            conversion_factor=None,
            comparable=False,
            incompatibility_reason=(
                "Unidade fiscal ausente; sem fator confiável para UN."
            ),
        )

    factor = _FACTOR_TO_UN.get(original_unit)
    if factor is None:
        return FiscalQuantityToUnResult(
            original_quantity=original_quantity,
            original_unit=original_unit,
            quantity_un=None,
            normalized_unit=None,
            conversion_factor=None,
            comparable=False,
            incompatibility_reason=(
                f"Unidade fiscal '{original_unit}' sem fator de conversão "
                "validado para UN (apenas UN/UN./MI)."
            ),
        )

    return FiscalQuantityToUnResult(
        original_quantity=original_quantity,
        original_unit=original_unit,
        quantity_un=original_quantity * factor,
        normalized_unit=NORMALIZED_UNIT,
        conversion_factor=factor,
        comparable=True,
        incompatibility_reason=None,
    )

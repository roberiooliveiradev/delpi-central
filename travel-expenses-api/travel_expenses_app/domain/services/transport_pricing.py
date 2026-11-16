"""Validated BRL and kilometre values for the travel-expenses domain."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


class ExpenseValueError(ValueError):
    """Expected invalid user-supplied financial/transport input."""


def _parse_nonnegative(value: object, *, label: str, maximum: Decimal) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ExpenseValueError(f"Informe {label}.")
    if isinstance(value, str):
        raw = value.strip().replace("\u00a0", " ").replace("R$", "").strip().replace(" ", "")
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", raw):
            raw = raw.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"\d+(?:,\d{1,2})?", raw):
            raw = raw.replace(",", ".")
        elif not re.fullmatch(r"\d+(?:\.\d{1,2})?", raw):
            raise ExpenseValueError(f"{label.capitalize()} inválido. Use um número com até duas casas decimais.")
    elif isinstance(value, (int, float, Decimal)):
        raw = str(value)
    else:
        raise ExpenseValueError(f"{label.capitalize()} inválido.")
    try:
        number = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise ExpenseValueError(f"{label.capitalize()} inválido.") from exc
    if not number.is_finite() or number < 0 or number > maximum:
        raise ExpenseValueError(f"{label.capitalize()} inválido ou fora do limite permitido.")
    return number.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_amount(value: object) -> Decimal:
    return _parse_nonnegative(value, label="o valor da despesa", maximum=Decimal("999999999999.99"))


def parse_distance_km(value: object) -> Decimal:
    distance = _parse_nonnegative(value, label="a quilometragem", maximum=Decimal("9999999.99"))
    if distance <= 0:
        raise ExpenseValueError("A quilometragem deve ser maior que zero.")
    return distance


def mileage_amount(distance_km: Decimal, rate_brl_per_km: Decimal) -> Decimal:
    if not rate_brl_per_km.is_finite() or rate_brl_per_km <= 0:
        raise ExpenseValueError("A tarifa de reembolso está inválida.")
    return (distance_km * rate_brl_per_km).quantize(CENT, rounding=ROUND_HALF_UP)

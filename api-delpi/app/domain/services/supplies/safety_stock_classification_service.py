"""Classificação de matérias-primas vs estoque de segurança cadastrado."""

from __future__ import annotations

TOLERANCE = 0.0001

PRIMARY_WAREHOUSE = "01"
AVAILABLE_BALANCE_WAREHOUSES = (PRIMARY_WAREHOUSE, "98", "99")
WORK_IN_PROCESS_WAREHOUSES = ("50", "98", "99")

STATUS_WITHOUT = "without_safety_stock"
STATUS_BELOW = "below_safety_stock"
STATUS_AT = "at_safety_stock"
STATUS_ABOVE = "above_safety_stock"

ALLOWED_STATUSES = frozenset(
    {
        STATUS_WITHOUT,
        STATUS_BELOW,
        STATUS_AT,
        STATUS_ABOVE,
    }
)


def classify_safety_stock_status(
    *,
    safety_stock: float | None,
    available_stock: float | None,
    primary_stock: float | None = None,
) -> str:
    """Classifica pela comparação ESTSEG × saldo disponível (armazéns 01 + 98 + 99)."""
    _ = primary_stock  # legado — ignorado quando available_stock é informado
    est = float(safety_stock or 0)
    available = float(
        available_stock if available_stock is not None else primary_stock or 0
    )

    if est <= 0:
        return STATUS_WITHOUT
    if available < est - TOLERANCE:
        return STATUS_BELOW
    if abs(available - est) <= TOLERANCE:
        return STATUS_AT
    return STATUS_ABOVE


def calculate_deficit_quantity(
    *,
    safety_stock: float | None,
    available_stock: float | None,
    primary_stock: float | None = None,
) -> float:
    """Déficit = ESTSEG − saldo disponível (01 + 98 + 99), nunca negativo."""
    _ = primary_stock
    est = float(safety_stock or 0)
    available = float(
        available_stock if available_stock is not None else primary_stock or 0
    )
    if est <= 0:
        return 0.0
    return max(est - available, 0.0)

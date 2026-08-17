"""FIFO stock allocation across open-order lines (same product + branch).

Mirrors the commercial MFE ``allocateStockToOrders`` rule so kanban counts,
ready-to-invoice detection and list badges share one source of truth.

Physical stock (``no_estoque``) is repeated per line by TOTVS; this service
splits it across competing lines by earliest delivery date.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

QUANTITY_DECIMALS = 3
_QUANTITY_SCALE = 10**QUANTITY_DECIMALS
_LINE_NUMERIC_RE = re.compile(r"(\d+|\D+)")


def round_quantity(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number:  # NaN
        return 0.0
    return round(number * _QUANTITY_SCALE) / _QUANTITY_SCALE


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date_only(raw: Any) -> str:
    text = _as_text(raw)
    if not text:
        return ""
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10]


def stock_group_key(item: Mapping[str, Any]) -> str:
    return f"{_as_text(item.get('filial'))}::{_as_text(item.get('produto'))}"


def line_key(item: Mapping[str, Any]) -> str:
    return (
        f"{_as_text(item.get('filial'))}::"
        f"{_as_text(item.get('pedido'))}::"
        f"{_as_text(item.get('linha'))}::"
        f"{_as_text(item.get('produto'))}"
    )


def _line_sort_parts(value: str) -> tuple:
    parts: list[tuple[int, Any]] = []
    for chunk in _LINE_NUMERIC_RE.findall(value or ""):
        if chunk.isdigit():
            parts.append((0, int(chunk)))
        else:
            parts.append((1, chunk))
    return tuple(parts)


def compare_lines_for_stock_allocation(
    a: Mapping[str, Any],
    b: Mapping[str, Any],
) -> int:
    date_a = _iso_date_only(a.get("data_entrega"))
    date_b = _iso_date_only(b.get("data_entrega"))
    if not date_a and not date_b:
        by_delivery = 0
    elif not date_a:
        by_delivery = 1
    elif not date_b:
        by_delivery = -1
    else:
        by_delivery = (date_a > date_b) - (date_a < date_b)
    if by_delivery != 0:
        return by_delivery

    pedido_a = _as_text(a.get("pedido"))
    pedido_b = _as_text(b.get("pedido"))
    if pedido_a != pedido_b:
        return (pedido_a > pedido_b) - (pedido_a < pedido_b)

    line_a = _as_text(a.get("linha"))
    line_b = _as_text(b.get("linha"))
    parts_a = _line_sort_parts(line_a)
    parts_b = _line_sort_parts(line_b)
    if parts_a != parts_b:
        return (parts_a > parts_b) - (parts_a < parts_b)
    return (line_a > line_b) - (line_a < line_b)


def _resolve_physical_stock(items: Sequence[Mapping[str, Any]]) -> float:
    peak = 0.0
    for item in items:
        try:
            stock = float(item.get("no_estoque") or 0)
        except (TypeError, ValueError):
            stock = 0.0
        if stock > peak:
            peak = stock
    return round_quantity(max(0.0, peak))


class OpenOrderStockAllocationService:
    """Pure FIFO allocation: writes ``estoque_alocado`` on each line copy."""

    def allocate(
        self,
        items: Sequence[Mapping[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        source = [dict(item) for item in (items or ()) if isinstance(item, Mapping)]
        if not source:
            return []

        groups: dict[str, list[dict[str, Any]]] = {}
        for item in source:
            key = stock_group_key(item)
            groups.setdefault(key, []).append(item)

        allocated_by_line: dict[str, float] = {}
        for group_items in groups.values():
            remaining = _resolve_physical_stock(group_items)
            sorted_items = sorted(
                group_items,
                key=lambda item: (
                    _iso_date_only(item.get("data_entrega")) or "9999-99-99",
                    _as_text(item.get("pedido")),
                    _line_sort_parts(_as_text(item.get("linha"))),
                    _as_text(item.get("linha")),
                ),
            )
            for item in sorted_items:
                try:
                    saldo_raw = float(item.get("saldo") or 0)
                except (TypeError, ValueError):
                    saldo_raw = 0.0
                saldo = round_quantity(max(0.0, saldo_raw))
                allocated = round_quantity(min(remaining, saldo))
                allocated_by_line[line_key(item)] = allocated
                remaining = round_quantity(remaining - allocated)

        return [
            {
                **item,
                "estoque_alocado": allocated_by_line.get(line_key(item), 0.0),
            }
            for item in source
        ]

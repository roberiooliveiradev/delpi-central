"""Montagem do histórico de preço unitário por fornecedor (últimos 12 meses)."""

from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_protheus_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def map_supplier_price_history_items(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normaliza linhas SD1 e devolve em ordem cronológica (ASC)."""
    mapped: list[dict[str, Any]] = []
    # Repositório devolve DESC; invertemos para o gráfico e variação do período.
    for row in reversed(raw_items):
        purchase_date = _format_protheus_date(row.get("entry_date"))
        if not purchase_date:
            purchase_date = _format_protheus_date(row.get("issue_date"))
        mapped.append(
            {
                "branch": str(row.get("branch") or "").strip(),
                "purchase_date": purchase_date,
                "issue_date": _format_protheus_date(row.get("issue_date")),
                "supplier_code": str(row.get("supplier_code") or "").strip(),
                "supplier_store": str(row.get("supplier_store") or "").strip(),
                "supplier_name": str(row.get("supplier_name") or "").strip(),
                "unit_price": _to_float(row.get("unit_price")),
                "quantity": _to_float(row.get("quantity")),
                "total_value": _to_float(row.get("total_value")),
                "invoice_number": str(row.get("invoice_number") or "").strip(),
                "invoice_series": str(row.get("invoice_series") or "").strip(),
            }
        )
    return mapped


def summarize_supplier_price_history(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {
            "total_purchases": 0,
            "min_unit_price": None,
            "max_unit_price": None,
            "first_unit_price": None,
            "last_unit_price": None,
            "variation_percent": None,
        }

    prices = [_to_float(item.get("unit_price")) for item in items]
    first_price = prices[0]
    last_price = prices[-1]
    variation_percent = None
    if first_price > 0:
        variation_percent = ((last_price - first_price) / first_price) * 100

    return {
        "total_purchases": len(items),
        "min_unit_price": min(prices),
        "max_unit_price": max(prices),
        "first_unit_price": first_price,
        "last_unit_price": last_price,
        "variation_percent": variation_percent,
    }

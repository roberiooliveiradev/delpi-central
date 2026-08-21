"""Mapeamento de OP atrasada da view PCP para o item de exceção do Portal.

Vive fora da análise de problemas porque a gestão à vista (home) continua
listando OP atrasada mesmo depois de a área virar uma grade de detectores.
"""

from __future__ import annotations

from typing import Any


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _severity(delay_days: int, critical_days: int) -> str:
    if delay_days >= critical_days:
        return "critical"
    return "attention"


def map_delayed_order(
    item: dict[str, Any],
    *,
    critical_days: int,
    title_template: str,
) -> dict[str, Any]:
    order = str(item.get("production_order") or "").strip()
    op_key = str(item.get("op_key") or "").strip() or order
    delay_days = _as_int(item.get("days_late"), 0)
    title = title_template.format(order=order or op_key, days=delay_days)
    return {
        "id": f"delayed-order:{op_key}",
        "kind": "delayed_order",
        "severity": _severity(delay_days, critical_days),
        "title": title,
        "product_code": str(item.get("product_code") or "").strip() or None,
        "product_description": str(
            item.get("product_description") or item.get("description") or ""
        ).strip()
        or None,
        "production_order": order or None,
        "op_key": op_key or None,
        "work_center": str(item.get("work_center") or "").strip() or None,
        "delay_days": delay_days,
        "branch": str(item.get("branch") or "").strip() or None,
        "metrics": {
            "planned_qty": _as_float(item.get("planned_qty")),
            "produced_qty": _as_float(item.get("produced_qty")),
            "pending_qty": _as_float(item.get("pending_qty")),
            "warehouse": str(item.get("warehouse") or "").strip() or None,
            "delivery_date": str(
                item.get("due_date") or item.get("delivery_date") or item.get("dt_entrega") or ""
            ).strip()
            or None,
            "has_balance": item.get("has_balance"),
            "is_open": item.get("is_open"),
        },
    }

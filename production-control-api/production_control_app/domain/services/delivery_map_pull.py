"""Normalização de linhas TOTVS para o mapa de entrega."""

from __future__ import annotations

from typing import Any

from production_control_app.application.services.delivery_map_settings import (
    delivery_map_product_prefixes,
)
from production_control_app.domain.services.product_code_scope import (
    product_code_matches_prefixes,
)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def normalize_pcp_order_row(item: dict[str, Any]) -> dict[str, Any] | None:
    """Converte item api-delpi em ordem canônica; None se fora do universo PA/saldo."""
    prefixes = delivery_map_product_prefixes()
    product_code = str(item.get("product_code") or "").strip()
    if not product_code_matches_prefixes(product_code, prefixes):
        return None

    pending_qty = round(_as_float(item.get("pending_qty")), 6)
    if pending_qty <= 0:
        return None

    production_order = str(item.get("production_order") or item.get("op_key") or "").strip()
    if not production_order:
        return None

    planned_qty = round(_as_float(item.get("planned_qty")), 6)
    produced_qty = round(_as_float(item.get("produced_qty")), 6)
    observation = str(item.get("observation") or "").strip() or None
    due_date = str(item.get("due_date") or "").strip()[:10] or None

    return {
        "production_order": production_order,
        "product_code": product_code,
        "product_description": str(item.get("product_description") or "").strip() or None,
        "due_date": due_date,
        "planned_qty": planned_qty,
        "produced_qty": produced_qty,
        "pending_qty": pending_qty,
        "observation": observation,
        "days_late": int(_as_float(item.get("days_late"))),
        "is_delayed": bool(item.get("is_delayed")),
    }


def normalize_pcp_order_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized = normalize_pcp_order_row(item)
        if normalized is None:
            continue
        key = normalized["production_order"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(normalized)
    return rows

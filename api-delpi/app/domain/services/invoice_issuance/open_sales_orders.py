"""Agrupa linhas de PV em aberto para o wizard de emissão."""

from __future__ import annotations

from typing import Any


def split_product_label(raw: Any) -> tuple[str, str]:
    text = str(raw or "").strip()
    if not text:
        return "", ""
    parts = text.split(None, 1)
    code = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else code
    return code, description


def _as_float(raw: Any) -> float:
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def group_open_sales_orders(
    lines: list[dict[str, Any]],
    *,
    branch_code: str,
) -> list[dict[str, Any]]:
    branch = str(branch_code or "").strip()
    grouped: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for raw in lines:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("filial") or "").strip() != branch:
            continue
        quantity_open = _as_float(raw.get("saldo"))
        if quantity_open <= 0:
            continue
        sales_order = str(raw.get("pedido") or "").strip()
        sales_order_item = str(raw.get("linha") or "").strip()
        if not sales_order or not sales_order_item:
            continue
        product_code, product_description = split_product_label(raw.get("produto"))
        if not product_code:
            continue
        unit_price = _as_float(raw.get("preco_venda"))
        line = {
            "sales_order": sales_order,
            "sales_order_item": sales_order_item,
            "customer_order_number": str(raw.get("pedido_cliente") or "").strip() or None,
            "product_code": product_code,
            "product_description": product_description,
            "quantity_ordered": _as_float(raw.get("quantidade")),
            "quantity_delivered": _as_float(raw.get("entregue")),
            "quantity_open": quantity_open,
            "unit_price": unit_price,
            "open_amount": _as_float(raw.get("valor_aberto")),
            "stock_on_hand": _as_float(raw.get("no_estoque")),
        }
        bucket = grouped.get(sales_order)
        if bucket is None:
            bucket = {
                "sales_order": sales_order,
                "customer_order_number": line["customer_order_number"],
                "branch_code": branch,
                "lines": [],
                "lines_count": 0,
                "open_quantity": 0.0,
                "open_amount": 0.0,
            }
            grouped[sales_order] = bucket
            order.append(sales_order)
        bucket["lines"].append(line)
        bucket["lines_count"] = len(bucket["lines"])
        bucket["open_quantity"] = round(float(bucket["open_quantity"]) + quantity_open, 4)
        bucket["open_amount"] = round(float(bucket["open_amount"]) + line["open_amount"], 2)
        if not bucket.get("customer_order_number") and line["customer_order_number"]:
            bucket["customer_order_number"] = line["customer_order_number"]
    return [grouped[key] for key in order]

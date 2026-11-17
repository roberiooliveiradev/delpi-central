"""Normalização estatística de vendas do produto para PCP (sem acesso a banco)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


VALID_MONTHS = frozenset({12, 24, 36})


def first_day_of_window(months: int, today: date) -> date:
    if months not in VALID_MONTHS:
        raise ValueError("Período inválido. Use 12, 24 ou 36 meses.")
    index = today.year * 12 + today.month - 1 - (months - 1)
    return date(index // 12, index % 12 + 1, 1)


def summarize_product_sales(
    rows: list[dict[str, Any]], *, months: int, today: date
) -> dict[str, Any]:
    """Agrupa SD2 positivo e SD1 devolvido, preenchendo meses sem movimento."""
    start = first_day_of_window(months, today)
    monthly: dict[str, dict[str, Any]] = {}
    for index in range(months):
        month_index = start.year * 12 + start.month - 1 + index
        key = f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"
        monthly[key] = {"month": key, "quantity": 0.0, "gross_quantity": 0.0, "returned_quantity": 0.0}

    customers: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        raw_month = str(row.get("month") or "").strip()
        month = raw_month[:4] + "-" + raw_month[4:6]
        if month not in monthly:
            continue
        gross = float(row.get("gross_quantity") or 0)
        returned = float(row.get("returned_quantity") or 0)
        net = gross - returned
        monthly[month]["gross_quantity"] += gross
        monthly[month]["returned_quantity"] += returned
        monthly[month]["quantity"] += net
        code = str(row.get("customer_code") or "").strip()
        store = str(row.get("customer_store") or "").strip()
        key = (code, store)
        customer = customers.setdefault(key, {
            "customer_code": code,
            "customer_store": store,
            "customer_name": str(row.get("customer_name") or "").strip() or code,
            "quantity": 0.0,
            "gross_quantity": 0.0,
            "returned_quantity": 0.0,
        })
        customer["quantity"] += net
        customer["gross_quantity"] += gross
        customer["returned_quantity"] += returned

    monthly_items = []
    for point in monthly.values():
        monthly_items.append({
            **point,
            "quantity": round(point["quantity"], 6),
            "gross_quantity": round(point["gross_quantity"], 6),
            "returned_quantity": round(point["returned_quantity"], 6),
        })
    customer_items = sorted(customers.values(), key=lambda item: (-item["gross_quantity"], item["customer_name"]))
    customer_items = [
        {**item, "quantity": round(item["quantity"], 6),
         "gross_quantity": round(item["gross_quantity"], 6),
         "returned_quantity": round(item["returned_quantity"], 6)}
        for item in customer_items
    ]
    gross_total = sum(item["gross_quantity"] for item in monthly_items)
    returned_total = sum(item["returned_quantity"] for item in monthly_items)
    net_total = gross_total - returned_total
    elapsed_days = (today - start).days + 1
    return {
        "period": {"months": months, "from": start.isoformat(), "to": today.isoformat()},
        "summary": {
            "total_quantity": round(net_total, 6),
            "gross_quantity": round(gross_total, 6),
            "returned_quantity": round(returned_total, 6),
            "weekly_average": round(net_total * 7 / elapsed_days, 6),
            "monthly_average": round(net_total / months, 6),
            "yearly_average": round(net_total * 12 / months, 6),
            "customer_count": len(customer_items),
            "active_month_count": sum(1 for item in monthly_items if item["gross_quantity"] > 0),
        },
        "monthly": monthly_items,
        "customers": customer_items,
    }

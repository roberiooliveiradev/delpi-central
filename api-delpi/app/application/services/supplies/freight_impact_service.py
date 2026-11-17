"""Composição de frete/compras por NF e competência.

Não calcular média de percentuais: o consolidado é soma(frete) / soma(compras).
NFs sem CT-e integram o denominador; NF sem base positiva tem % indisponível.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

CENT = Decimal("0.01")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (ValueError, InvalidOperation):
        return Decimal("0")


def _number(value: Decimal) -> float:
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _percent(numerator: Decimal, denominator: Decimal) -> float | None:
    return _number(numerator * 100 / denominator) if denominator > 0 else None


def _iso_date(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return ""


def compose_freight_impact(
    rows: list[dict[str, Any]],
    *,
    branches: list[str],
    date_from: str,
    date_to: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Composição determinística; todos os totais usam o dataset completo."""
    invoices: list[dict[str, Any]] = []
    monthly: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {"purchase_cost": Decimal("0"), "freight_cost": Decimal("0"), "invoices": 0}
    )
    purchases = Decimal("0")
    freights = Decimal("0")
    with_freight = 0
    invalid_base = 0

    for raw in rows:
        purchase = _decimal(raw.get("purchase_cost"))
        freight = _decimal(raw.get("freight_cost"))
        valid = purchase > 0 and freight >= 0
        issue_date = _iso_date(raw.get("issue_date"))
        invoice = {
            "branch": str(raw.get("branch") or "").strip(),
            "invoice_document": str(raw.get("invoice_document") or "").strip(),
            "invoice_series": str(raw.get("invoice_series") or "").strip(),
            "supplier_code": str(raw.get("supplier_code") or "").strip(),
            "supplier_store": str(raw.get("supplier_store") or "").strip(),
            "supplier_name": str(raw.get("supplier_name") or "").strip(),
            "issue_date": issue_date,
            "purchase_cost": _number(purchase),
            "freight_cost": _number(freight),
            "cte_count": int(raw.get("cte_count") or 0),
            "freight_pct": _percent(freight, purchase) if valid else None,
            "calculation_status": "valid" if valid else "invalid_base",
        }
        invoices.append(invoice)
        if not valid:
            invalid_base += 1
            continue
        purchases += purchase
        freights += freight
        if freight > 0:
            with_freight += 1
        bucket = monthly[issue_date[:7]]
        bucket["purchase_cost"] += purchase
        bucket["freight_cost"] += freight
        bucket["invoices"] += 1

    invoices.sort(
        key=lambda item: (
            item["freight_pct"] is None,
            -(item["freight_pct"] or 0),
            item["branch"],
            item["invoice_document"],
            item["invoice_series"],
            item["supplier_code"],
        )
    )
    total = len(invoices)
    start = (page - 1) * page_size
    series = [
        {
            "period": period,
            "purchase_cost": _number(values["purchase_cost"]),
            "freight_cost": _number(values["freight_cost"]),
            "freight_pct": _percent(values["freight_cost"], values["purchase_cost"]),
            "invoices": values["invoices"],
        }
        for period, values in sorted(monthly.items())
    ]
    return {
        "source": "SF1010+SD1010+SF8010",
        "method": "DLP02R01_cost",
        "scope": "domestic_purchases_sped",
        "filters": {
            "branches": branches,
            "date_from": date_from,
            "date_to": date_to,
            "date_field": "F1_EMISSAO",
        },
        "summary": {
            "invoice_count": total,
            "valid_invoice_count": total - invalid_base,
            "invalid_base_count": invalid_base,
            "with_freight_count": with_freight,
            "without_freight_count": total - invalid_base - with_freight,
            "purchases_total": _number(purchases),
            "freight_total": _number(freights),
            "freight_pct": _percent(freights, purchases),
        },
        "monthly": series,
        "items": invoices[start:start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

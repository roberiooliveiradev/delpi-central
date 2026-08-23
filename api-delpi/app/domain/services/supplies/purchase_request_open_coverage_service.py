"""Cobertura TOTVS pura de solicitações de compra em aberto (SC1).

Fatos por produto: saldo SB2 (01+98+99) + SC7 elegível − SD4 elegível + ESTSEG (SBZ).
A SC1 não entra na projeção — o consumidor classifica excesso e falta.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    enrich_open_purchase_orders,
    enrich_open_purchase_requests,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    enrich_open_commitments,
)


def _group_by_product(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        code = str(row.get("product_code") or "").strip()
        if code:
            grouped[code].append(row)
    return grouped


def _unit_kwargs(stock: dict[str, Any] | None, fallback_unit: str | None) -> dict[str, Any]:
    source = stock or {}
    primary = str(source.get("unit") or fallback_unit or "").strip() or None
    return {
        "primary_unit": primary,
        "secondary_unit": str(source.get("secondary_unit") or "").strip() or None,
        "conversion_factor": source.get("conversion_factor"),
        "conversion_type": str(source.get("conversion_type") or "").strip() or None,
    }


def _coverage_for_product(
    *,
    stock: dict[str, Any] | None,
    orders: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
    fallback_unit: str | None,
) -> dict[str, Any]:
    kwargs = _unit_kwargs(stock, fallback_unit)
    _enriched_orders, order_totals = enrich_open_purchase_orders(
        orders=orders,
        **kwargs,
    )
    _enriched_commitments, commitment_totals = enrich_open_commitments(
        commitments=commitments,
        **kwargs,
    )
    available = float((stock or {}).get("available_stock") or 0)
    safety_stock = float((stock or {}).get("safety_stock") or 0)
    open_purchase = float(order_totals.get("eligible_open_quantity") or 0)
    open_commitment = float(commitment_totals.get("eligible_open_quantity") or 0)
    return {
        "available_stock": available,
        "safety_stock": safety_stock,
        "open_purchase_order_quantity": open_purchase,
        "open_commitment_quantity": open_commitment,
        "projected_balance": available + open_purchase - open_commitment,
        "primary_unit": kwargs["primary_unit"] or "",
    }


def _ensure_coverage(
    *,
    code: str,
    stock: dict[str, Any] | None,
    orders_by_code: dict[str, list[dict[str, Any]]],
    commitments_by_code: dict[str, list[dict[str, Any]]],
    fallback_unit: str | None,
    coverage_by_code: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if code not in coverage_by_code:
        coverage_by_code[code] = _coverage_for_product(
            stock=stock,
            orders=orders_by_code.get(code, []),
            commitments=commitments_by_code.get(code, []),
            fallback_unit=fallback_unit,
        )
    return coverage_by_code[code]


def build_purchase_request_open_coverage(
    *,
    requests: list[dict[str, Any]],
    stocks: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Monta o dump SC1 + totais do produto (sem classificar excesso/falta)."""
    stocks_by_code = {
        str(row.get("product_code") or "").strip(): row
        for row in stocks
        if str(row.get("product_code") or "").strip()
    }
    orders_by_code = _group_by_product(orders)
    commitments_by_code = _group_by_product(commitments)
    coverage_by_code: dict[str, dict[str, Any]] = {}
    items: list[dict[str, Any]] = []

    for raw in requests:
        code = str(raw.get("product_code") or "").strip()
        if not code:
            continue
        stock = stocks_by_code.get(code)
        unit_kwargs = _unit_kwargs(stock, str(raw.get("unit") or "").strip() or None)
        enriched = enrich_open_purchase_requests(requests=[raw], **unit_kwargs)[0]
        coverage = _ensure_coverage(
            code=code,
            stock=stock,
            orders_by_code=orders_by_code,
            commitments_by_code=commitments_by_code,
            fallback_unit=str(raw.get("unit") or "").strip() or None,
            coverage_by_code=coverage_by_code,
        )
        items.append(
            {
                "branch": str(enriched.get("branch") or "").strip(),
                "request_number": str(enriched.get("request_number") or "").strip(),
                "request_item": str(enriched.get("request_item") or "").strip(),
                "product_code": code,
                "product_description": str(enriched.get("product_description") or "").strip(),
                "warehouse": str(enriched.get("warehouse") or "").strip(),
                "unit": str(enriched.get("unit") or "").strip(),
                "open_quantity": float(enriched.get("open_quantity") or 0),
                "open_quantity_primary_unit": enriched.get("open_quantity_primary_unit"),
                "unit_compatible": bool(enriched.get("unit_compatible")),
                "issue_date": enriched.get("issue_date"),
                "required_date": enriched.get("required_date"),
                "supplier_code": str(enriched.get("supplier_code") or "").strip(),
                "supplier_name": str(enriched.get("supplier_name") or "").strip(),
                "product_coverage": coverage,
            }
        )

    products: list[dict[str, Any]] = []
    for code, stock in stocks_by_code.items():
        coverage = _ensure_coverage(
            code=code,
            stock=stock,
            orders_by_code=orders_by_code,
            commitments_by_code=commitments_by_code,
            fallback_unit=str(stock.get("unit") or "").strip() or None,
            coverage_by_code=coverage_by_code,
        )
        products.append(
            {
                "product_code": code,
                "product_description": str(stock.get("product_description") or "").strip(),
                "unit": str(stock.get("unit") or coverage.get("primary_unit") or "").strip(),
                "product_coverage": coverage,
            }
        )
    return {"items": items, "products": products}

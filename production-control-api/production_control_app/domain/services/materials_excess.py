"""Classifica SC1 em excesso e produtos com solicitações insuficientes.

Necessário da SC1 = max(0, ESTSEG − projetado), com
projetado = saldo + pedidos − empenhos. A SC1 não entra no projetado.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from typing import Any

TOLERANCE = 0.0001


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _iso_date(value: Any) -> date | None:
    text = _text(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _coverage(item: dict[str, Any]) -> dict[str, Any]:
    block = item.get("product_coverage")
    return block if isinstance(block, dict) else {}


def _open_quantity(item: dict[str, Any]) -> float:
    primary = item.get("open_quantity_primary_unit")
    if primary is None:
        return max(_number(item.get("open_quantity")), 0.0)
    return max(_number(primary), 0.0)


def needed_from_sc1(coverage: dict[str, Any]) -> float:
    """Quanto ainda falta da SC1 para cobrir empenhos e o ESTSEG."""
    projected = _number(coverage.get("projected_balance"))
    safety_stock = max(_number(coverage.get("safety_stock")), 0.0)
    return max(0.0, safety_stock - projected)


@dataclass(frozen=True, slots=True)
class EliminableRequest:
    request_number: str
    request_item: str
    product_code: str
    product_description: str
    unit: str
    warehouse: str
    supplier_name: str
    open_quantity: float
    required_date: date | None
    issue_date: date | None
    available_stock: float
    safety_stock: float
    open_purchase_order_quantity: float
    open_commitment_quantity: float
    projected_balance: float
    needed_from_sc1: float

    @property
    def id(self) -> str:
        return f"{self.request_number}/{self.request_item}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "excess",
            "request_number": self.request_number,
            "request_item": self.request_item,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "unit": self.unit,
            "warehouse": self.warehouse,
            "supplier_name": self.supplier_name,
            "open_quantity": round(self.open_quantity, 6),
            "required_date": self.required_date.isoformat() if self.required_date else None,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "available_stock": round(self.available_stock, 6),
            "safety_stock": round(self.safety_stock, 6),
            "open_purchase_order_quantity": round(self.open_purchase_order_quantity, 6),
            "open_commitment_quantity": round(self.open_commitment_quantity, 6),
            "projected_balance": round(self.projected_balance, 6),
            "needed_from_sc1": round(self.needed_from_sc1, 6),
        }


@dataclass(frozen=True, slots=True)
class ShortageProduct:
    product_code: str
    product_description: str
    unit: str
    available_stock: float
    safety_stock: float
    open_purchase_order_quantity: float
    open_commitment_quantity: float
    projected_balance: float
    open_sc1_quantity: float
    needed_from_sc1: float
    shortage_quantity: float

    @property
    def id(self) -> str:
        return self.product_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "shortage",
            "product_code": self.product_code,
            "product_description": self.product_description,
            "unit": self.unit,
            "available_stock": round(self.available_stock, 6),
            "safety_stock": round(self.safety_stock, 6),
            "open_purchase_order_quantity": round(self.open_purchase_order_quantity, 6),
            "open_commitment_quantity": round(self.open_commitment_quantity, 6),
            "projected_balance": round(self.projected_balance, 6),
            "open_sc1_quantity": round(self.open_sc1_quantity, 6),
            "needed_from_sc1": round(self.needed_from_sc1, 6),
            "shortage_quantity": round(self.shortage_quantity, 6),
        }


def _to_eliminable(row: dict[str, Any], coverage: dict[str, Any], needed: float) -> EliminableRequest:
    return EliminableRequest(
        request_number=_text(row.get("request_number")),
        request_item=_text(row.get("request_item")),
        product_code=_text(row.get("product_code")),
        product_description=_text(row.get("product_description")),
        unit=_text(row.get("unit") or coverage.get("primary_unit")),
        warehouse=_text(row.get("warehouse")),
        supplier_name=_text(row.get("supplier_name")),
        open_quantity=_open_quantity(row),
        required_date=_iso_date(row.get("required_date")),
        issue_date=_iso_date(row.get("issue_date")),
        available_stock=_number(coverage.get("available_stock")),
        safety_stock=_number(coverage.get("safety_stock")),
        open_purchase_order_quantity=_number(coverage.get("open_purchase_order_quantity")),
        open_commitment_quantity=_number(coverage.get("open_commitment_quantity")),
        projected_balance=_number(coverage.get("projected_balance")),
        needed_from_sc1=needed,
    )


def classify_fully_eliminable(items: list[dict[str, Any]]) -> list[EliminableRequest]:
    """FIFO por produto: mantém SC1 até cobrir ESTSEG − projetado; o resto sai."""
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for item in items:
        code = _text(item.get("product_code"))
        if not code:
            continue
        groups.setdefault(code, []).append(item)

    result: list[EliminableRequest] = []
    for rows in groups.values():
        coverage = _coverage(rows[0])
        needed = needed_from_sc1(coverage)
        remaining_need = needed
        for row in rows:
            open_qty = _open_quantity(row)
            if remaining_need > TOLERANCE:
                remaining_need = max(0.0, remaining_need - open_qty)
                continue
            result.append(_to_eliminable(row, coverage, needed))
    return result


def classify_shortage_products(
    items: list[dict[str, Any]],
    products: list[dict[str, Any]],
) -> list[ShortageProduct]:
    """Produtos cuja SC1 em aberto não chega no ESTSEG (ou não há SC1)."""
    open_by_code: dict[str, float] = {}
    description_by_code: dict[str, str] = {}
    for item in items:
        code = _text(item.get("product_code"))
        if not code:
            continue
        open_by_code[code] = open_by_code.get(code, 0.0) + _open_quantity(item)
        if not description_by_code.get(code):
            description_by_code[code] = _text(item.get("product_description"))

    result: list[ShortageProduct] = []
    seen: set[str] = set()
    for product in products:
        code = _text(product.get("product_code"))
        if not code or code in seen:
            continue
        seen.add(code)
        coverage = _coverage(product)
        needed = needed_from_sc1(coverage)
        open_sc1 = open_by_code.get(code, 0.0)
        gap = max(0.0, needed - open_sc1)
        if gap <= TOLERANCE:
            continue
        result.append(
            ShortageProduct(
                product_code=code,
                product_description=_text(
                    product.get("product_description") or description_by_code.get(code)
                ),
                unit=_text(product.get("unit") or coverage.get("primary_unit")),
                available_stock=_number(coverage.get("available_stock")),
                safety_stock=_number(coverage.get("safety_stock")),
                open_purchase_order_quantity=_number(
                    coverage.get("open_purchase_order_quantity")
                ),
                open_commitment_quantity=_number(coverage.get("open_commitment_quantity")),
                projected_balance=_number(coverage.get("projected_balance")),
                open_sc1_quantity=open_sc1,
                needed_from_sc1=needed,
                shortage_quantity=gap,
            )
        )
    return result

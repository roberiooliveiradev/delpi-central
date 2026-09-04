# app/domain/entities/product_sales_open_orders.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductSalesOpenOrders:
    """Carteira de pedidos em aberto do produto (linhas + totais)."""

    items: list[dict[str, Any]] = field(default_factory=list)
    quantity: float = 0.0
    value: float = 0.0
    orders: int = 0
    page: int = 1
    page_size: int = 50
    total: int = 0
    total_pages: int = 0

    def as_payload(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "summary": {
                "quantity": self.quantity,
                "value": self.value,
                "orders": self.orders,
            },
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
            # Compatível com consumidores que liam só agregados no root.
            "quantity": self.quantity,
            "value": self.value,
            "orders": self.orders,
        }

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class CustomerOutboundInvoiceItem:
    item: str
    product_code: str
    product_description: str
    quantity: float
    unit: str
    unit_price: float
    total_value: float
    sales_order: str
    sales_order_item: str
    customer_order: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "item": self.item,
            "product_code": self.product_code,
            "product_description": self.product_description,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "total_value": self.total_value,
            "sales_order": self.sales_order,
            "sales_order_item": self.sales_order_item,
            "customer_order": self.customer_order,
        }


@dataclass(frozen=True)
class CustomerOutboundInvoice:
    key: str
    branch: str
    invoice_number: str
    invoice_series: str
    issue_date: str
    customer_code: str
    customer_store: str
    customer_name: str
    total_value: float
    situation: str
    sales_order: str
    customer_order: str
    item_count: int
    access_key: Optional[str] = None
    carrier: Optional[str] = None
    items: tuple[CustomerOutboundInvoiceItem, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "branch": self.branch,
            "invoice_number": self.invoice_number,
            "invoice_series": self.invoice_series,
            "issue_date": self.issue_date,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "total_value": self.total_value,
            "situation": self.situation,
            "sales_order": self.sales_order,
            "customer_order": self.customer_order,
            "item_count": self.item_count,
            "access_key": self.access_key,
            "carrier": self.carrier,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass(frozen=True)
class CustomerOutboundInvoiceSummary:
    total_billed_value: float
    invoice_count: int
    last_invoice_date: Optional[str]
    last_invoice_value: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_billed_value": self.total_billed_value,
            "invoice_count": self.invoice_count,
            "last_invoice_date": self.last_invoice_date,
            "last_invoice_value": self.last_invoice_value,
        }


@dataclass(frozen=True)
class CustomerOutboundInvoicesPage:
    summary: CustomerOutboundInvoiceSummary
    invoices: tuple[CustomerOutboundInvoice, ...]
    page: int
    page_size: int
    total: int
    total_pages: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "invoices": [invoice.to_dict() for invoice in self.invoices],
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "total_pages": self.total_pages,
            },
        }

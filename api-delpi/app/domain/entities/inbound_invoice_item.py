# app/domain/entities/inbound_invoice_item.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class InboundInvoiceItem:

    branch: str
    invoice_number: str
    invoice_series: str
    item: str
    issue_date: str

    product_code: str
    product_description: str
    unit: str

    supplier_code: str
    supplier_name: Optional[str]

    quantity: float
    unit_price: float
    total_value: float
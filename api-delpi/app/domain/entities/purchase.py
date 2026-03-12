# app/domain/entities/purchase.py
from dataclasses import dataclass


@dataclass
class Purchase:

    order_number: str
    branch: str
    issue_date: str

    supplier_code: str
    store: str
    supplier_name: str | None

    product_code: str

    ordered_quantity: float
    unit_price: float
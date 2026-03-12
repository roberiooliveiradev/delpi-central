# app/domain/entities/product_sales_billing.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductSalesBilling:

    value: float
    documents: int

    first_billing_date: Optional[str]
    last_billing_date: Optional[str]
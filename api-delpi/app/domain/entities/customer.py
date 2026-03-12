# app/domain/entities/customer.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:

    product_code: str
    product_description: Optional[str]
    unit: Optional[str]

    customer_code: str
    store: str
    customer_name: Optional[str]
    blocked: Optional[str]

    customer_product_code: Optional[str]
    customer_product_description: Optional[str]

    registered_price: Optional[float]
    registered_price_date: Optional[str]

    last_sale_price: Optional[float]
    last_sale_date: Optional[str]
    total_quantity: Optional[float]
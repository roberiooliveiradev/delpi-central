# app/domain/entities/product_sales_summary.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductSalesSummary:

    product_code: str
    product_description: Optional[str]
    unit: Optional[str]

    total_quantity: float
    total_value: float
    average_price: float

    documents: int

    first_sale_date: Optional[str]
    last_sale_date: Optional[str]
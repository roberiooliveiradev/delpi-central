# app/domain/entities/sale/sale_order.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class SaleOrder:
    branch: str
    order_number: str
    description: str
    revision_number: Optional[str]
    date: Optional[str] = None
    user_code: Optional[str] = None
    seller_code: Optional[str] = None
    costumer_code: Optional[str] = None
    stage: Optional[str] = None
    product_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
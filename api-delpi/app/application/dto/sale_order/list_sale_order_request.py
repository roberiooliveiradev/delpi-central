# app/application/dto/sale_order/list_sale_order_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListSaleOrderRequest:
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
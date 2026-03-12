# app/application/dto/list_product_stock_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductStockRequest:

    code: str
    page: int
    page_size: int

    branch: Optional[str] = None
    location: Optional[str] = None
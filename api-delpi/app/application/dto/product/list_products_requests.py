# app/application/dto/list_products_requests.py
from  dataclasses import dataclass
from typing import Optional

@dataclass
class ListProductsRequest:
    code: Optional[str] = None
    group_code: Optional[str] = None
    description: Optional[str] = None
    customer_reference: Optional[str] = None
    page: int = 1
    page_size: int = 50
    sort: Optional[str] = None
    direction: Optional[str] = "asc"
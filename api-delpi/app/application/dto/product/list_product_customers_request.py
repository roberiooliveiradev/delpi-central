# app/application/dto/list_product_customers_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductCustomersRequest:

    code: str
    page: Optional[int] = 1
    page_size: Optional[int] = 50
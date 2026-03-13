# app/application/dto/list_product_internal_movements_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductInternalMovementsRequest:

    code: str
    page: int = 1
    page_size: int = 50

    date_start: Optional[str] = None
    date_end: Optional[str] = None

    branch: Optional[str] = None
    location: Optional[str] = None

    tm: Optional[str] = None
    op: Optional[str] = None
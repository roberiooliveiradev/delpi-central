# app/application/dto/list_product_parents_request.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductParentsRequest:

    code: str
    max_depth: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
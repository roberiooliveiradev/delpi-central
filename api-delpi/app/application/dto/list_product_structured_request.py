# app/application/dto/list_product_structured_request.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductStructureRequest:
    code: str
    max_depth: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None

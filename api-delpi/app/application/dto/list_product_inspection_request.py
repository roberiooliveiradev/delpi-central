# app/application/dto/list_product_inspection_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductInspectionRequest:

    code: str

    page: Optional[int] = None
    page_size: Optional[int] = None

    max_depth: Optional[int] = None
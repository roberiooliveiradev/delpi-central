# app/application/dto/list_product_guide_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductGuideRequest:

    code: str
    branch: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    max_depth: Optional[int] = None
# app/application/dto/list_product_guide_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductGuideRequest:

    code: str
    page: int = 1
    page_size: int = 50
    branch: Optional[str] = None
    max_depth: int = 10
# app/application/dto/list_product_inspection_request.py
from dataclasses import dataclass


@dataclass
class ListProductInspectionRequest:
    code: str
    max_depth: int = 10
# app/application/dto/list_product_suppliers_request.py
from dataclasses import dataclass


@dataclass
class ListProductSuppliersRequest:

    code: str
    page: int = 1
    page_size: int = 50
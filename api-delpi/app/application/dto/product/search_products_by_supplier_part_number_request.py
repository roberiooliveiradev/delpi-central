# app/application/dto/product/search_products_by_supplier_part_number_request.py
from dataclasses import dataclass


@dataclass
class SearchProductsBySupplierPartNumberRequest:
    supplier_part_number: str
    supplier_code: str | None = None
    page: int = 1
    page_size: int = 50

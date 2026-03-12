# app/application/dto/list_product_purchases_request.py
from dataclasses import dataclass


@dataclass
class ListProductPurchasesRequest:

    code: str
    page: int
    page_size: int
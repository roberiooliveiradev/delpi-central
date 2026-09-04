# app/application/dto/get_product_sales_open_orders_request.py
from dataclasses import dataclass


@dataclass
class GetProductSalesOpenOrdersRequest:

    code: str
    branch: str | None = None
    page: int = 1
    page_size: int = 50

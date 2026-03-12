# app/application/dto/get_product_sales_open_orders_request.py
from dataclasses import dataclass


@dataclass
class GetProductSalesOpenOrdersRequest:

    code: str
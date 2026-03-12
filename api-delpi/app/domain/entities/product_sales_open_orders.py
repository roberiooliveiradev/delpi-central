# app/domain/entities/product_sales_open_orders.py
from dataclasses import dataclass


@dataclass
class ProductSalesOpenOrders:

    quantity: float
    value: float
    orders: int
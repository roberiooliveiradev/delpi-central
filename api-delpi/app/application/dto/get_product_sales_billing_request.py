# app/application/dto/get_product_sales_billing_request.py
from dataclasses import dataclass


@dataclass
class GetProductSalesBillingRequest:

    code: str
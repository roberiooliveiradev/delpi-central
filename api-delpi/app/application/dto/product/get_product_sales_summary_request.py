# app/application/dto/get_product_sales_summary_request.py
from dataclasses import dataclass


@dataclass
class GetProductSalesSummaryRequest:

    code: str
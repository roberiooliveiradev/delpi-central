# app/application/dto/get_product_pricing_request.py
from dataclasses import dataclass


@dataclass
class GetProductPricingRequest:

    code: str
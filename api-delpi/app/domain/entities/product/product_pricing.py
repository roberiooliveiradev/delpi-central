# app/domain/entities/product_pricing.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductPricingItem:

    table_code: str
    table_description: Optional[str]

    sale_price: float
    max_price: float

    discount_value: float
    discount_percent: float

    lot_quantity: float

    state: Optional[str]
    operation_type: Optional[str]
    currency: Optional[str]

    valid_from: Optional[str]
    active: Optional[str]


@dataclass
class ProductPricing:

    product_code: str
    product_description: Optional[str]
    unit: Optional[str]

    prices: list[ProductPricingItem]
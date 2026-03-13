# app/domain/entities/stock.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Stock:

    product_code: str
    branch: str
    warehouse: str

    current_quantity: float
    committed_quantity: float
    reserved_quantity: float
    available_quantity: float

    physical_location: Optional[str]
    default_warehouse: Optional[str]
    cost_center: Optional[str]
    warehouse_section: Optional[str]
# app/domain/entities/internal_movement.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class InternalMovement:

    branch: str
    location: str
    document: str
    issue_date: str

    product_code: str
    product_description: str
    unit: str

    movement_type: str
    cf: Optional[str]

    quantity: float

    production_order: Optional[str]
    user_name: Optional[str]

    movement_category: Optional[str] = None
    movement_direction: Optional[str] = None
    movement_label: Optional[str] = None
    inventory_adjustment_nature: Optional[str] = None

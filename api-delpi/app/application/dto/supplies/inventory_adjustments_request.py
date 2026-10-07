"""Request dos ajustes de inventário (SD3 doc='INVENT')."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.services.supplies.inventory_adjustment_service import (
    normalize_nature,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class InventoryAdjustmentsRequest:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch: Optional[str] = None
    product_code: Optional[str] = None
    warehouse: Optional[str] = None
    nature: Optional[str] = None
    page: int = 1
    page_size: int = 50

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
        self.nature = normalize_nature(self.nature)
        if self.product_code:
            self.product_code = str(self.product_code).strip() or None
        if self.warehouse:
            self.warehouse = str(self.warehouse).strip() or None

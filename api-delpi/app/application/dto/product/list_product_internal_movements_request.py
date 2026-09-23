# app/application/dto/list_product_internal_movements_request.py
from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ListProductInternalMovementsRequest:

    code: str
    page: int = 1
    page_size: int = 50

    date_start: Optional[str] = None
    date_end: Optional[str] = None

    branch: Optional[str] = None
    location: Optional[str] = None

    tm: Optional[str] = None
    op: Optional[str] = None
    kind: Optional[str] = None

    def __post_init__(self) -> None:
        from app.domain.totvs.protheus_internal_movements import (
            warehouse_transfer_cfs_for_kind,
        )

        self.branch = optional_concrete_branch(self.branch)
        kind = (self.kind or "").strip().lower() or None
        self.kind = kind
        warehouse_transfer_cfs_for_kind(kind)

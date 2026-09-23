"""DTOs — saldos de estoque por armazém."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.totvs.protheus_branches import normalize_optional_branch_codes
from app.domain.totvs.protheus_product_codes import normalize_product_codes


@dataclass
class StockBalancesQueryRequest:
    branches: tuple[str, ...] | list[str] | str | None = field(default_factory=tuple)
    warehouse: str | None = None
    only_positive: bool = True

    def __post_init__(self) -> None:
        self.branches = normalize_optional_branch_codes(self.branches)
        if self.warehouse is not None:
            self.warehouse = str(self.warehouse).strip() or None


@dataclass
class StockBalancesItemsRequest(StockBalancesQueryRequest):
    page: int = 1
    page_size: int = 50
    sort: str = "stock_value_desc"
    product_codes: tuple[str, ...] | list[str] | str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.page = max(1, int(self.page or 1))
        self.page_size = min(500, max(1, int(self.page_size or 50)))
        self.sort = (self.sort or "stock_value_desc").strip().lower()
        self.product_codes = normalize_product_codes(self.product_codes)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

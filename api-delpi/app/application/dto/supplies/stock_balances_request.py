"""DTOs — saldos de estoque por armazém."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class StockBalancesQueryRequest:
    branch: str | None = None
    warehouse: str | None = None
    only_positive: bool = True

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
        if self.warehouse is not None:
            self.warehouse = str(self.warehouse).strip() or None


@dataclass
class StockBalancesItemsRequest(StockBalancesQueryRequest):
    page: int = 1
    page_size: int = 50
    sort: str = "stock_value_desc"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.page = max(1, int(self.page or 1))
        self.page_size = min(500, max(1, int(self.page_size or 50)))
        self.sort = (self.sort or "stock_value_desc").strip().lower()

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

"""DTOs — matérias-primas sem giro."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.services.supplies.non_moving_stock_service import (
    APPROVED_WAREHOUSE_SCOPE,
)
from app.domain.totvs.protheus_branches import normalize_optional_branch_codes
from app.domain.totvs.protheus_product_codes import normalize_product_codes

_APPROVED_BRANCHES = ("01", "02")

_VALID_STATUSES = {
    "WITH_CONSUMPTION",
    "NO_CONSUMPTION_12M",
    "NO_CONSUMPTION_IN_PERIOD",
    "INSUFFICIENT_HISTORY",
}


def _normalize_warehouses(
    value: tuple[str, ...] | list[str] | str | None,
) -> tuple[str, ...]:
    if value is None:
        return APPROVED_WAREHOUSE_SCOPE
    raw = (value,) if isinstance(value, str) else tuple(value)
    out: list[str] = []
    for item in raw:
        for token in str(item).split(","):
            code = token.strip()
            if code:
                out.append(code.zfill(2) if code.isdigit() else code)
    if not out:
        return APPROVED_WAREHOUSE_SCOPE
    invalid = [w for w in out if w not in APPROVED_WAREHOUSE_SCOPE]
    if invalid:
        raise ValueError(
            "warehouse outside the approved scope "
            f"{APPROVED_WAREHOUSE_SCOPE}: {invalid}"
        )
    return tuple(dict.fromkeys(out))


def _normalize_ymd(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError("dates must use the YYYY-MM-DD format")
    return text


@dataclass
class NonMovingStockQueryRequest:
    branches: tuple[str, ...] | list[str] | str | None = field(
        default_factory=tuple
    )
    warehouses: tuple[str, ...] | list[str] | str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        self.branches = (
            normalize_optional_branch_codes(self.branches)
            or _APPROVED_BRANCHES
        )
        self.warehouses = _normalize_warehouses(self.warehouses)
        self.start_date = _normalize_ymd(self.start_date)
        self.end_date = _normalize_ymd(self.end_date)


@dataclass
class NonMovingStockItemsRequest(NonMovingStockQueryRequest):
    page: int = 1
    page_size: int = 50
    sort: str = "stock_value_desc"
    product_codes: tuple[str, ...] | list[str] | str | None = None
    turnover_status: str | None = None
    blocked: bool | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.page = max(1, int(self.page or 1))
        self.page_size = min(500, max(1, int(self.page_size or 50)))
        self.sort = (self.sort or "stock_value_desc").strip().lower()
        self.product_codes = normalize_product_codes(self.product_codes)
        if self.turnover_status:
            status = str(self.turnover_status).strip().upper()
            if status not in _VALID_STATUSES:
                raise ValueError(f"invalid turnover_status: {status}")
            self.turnover_status = status

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

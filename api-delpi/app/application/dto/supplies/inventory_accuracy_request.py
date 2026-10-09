"""DTOs — acuracidade do inventário físico."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.totvs.protheus_branches import normalize_optional_branch_codes

_APPROVED_BRANCHES = ("01", "02")

_VALID_OUTCOMES = {"accurate", "divergent", "excluded"}


def _normalize_search(value: str | None, max_length: int = 120) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) > max_length:
        raise ValueError(
            f"search exceeds the {max_length}-character limit"
        )
    return text


def _normalize_ymd(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError("dates must use the YYYY-MM-DD format")
    return text


@dataclass
class InventoryAccuracyQueryRequest:
    branches: tuple[str, ...] | list[str] | str | None = field(
        default_factory=tuple
    )
    month: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        self.branches = (
            normalize_optional_branch_codes(self.branches)
            or _APPROVED_BRANCHES
        )
        if self.month:
            self.month = str(self.month).strip()
        self.start_date = _normalize_ymd(self.start_date)
        self.end_date = _normalize_ymd(self.end_date)


@dataclass
class InventoryAccuracyItemsRequest(InventoryAccuracyQueryRequest):
    page: int = 1
    page_size: int = 50
    sort: str = "count_date_desc"
    outcome: str | None = None
    search: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.page = max(1, int(self.page or 1))
        self.page_size = min(500, max(1, int(self.page_size or 50)))
        self.sort = (self.sort or "count_date_desc").strip().lower()
        self.search = _normalize_search(self.search)
        if self.outcome:
            outcome = str(self.outcome).strip().lower()
            if outcome not in _VALID_OUTCOMES:
                raise ValueError(f"invalid outcome: {outcome}")
            self.outcome = outcome

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

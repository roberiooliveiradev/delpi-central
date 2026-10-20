"""DTOs — supplier master-data read requests (Supplies portal)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SuppliersListRequest:
    query: str | None = None
    state: str | None = None
    blocked: bool | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "supplier_name"
    sort_dir: str = "asc"

    def __post_init__(self) -> None:
        if self.query is not None:
            query = str(self.query).strip()
            if query and len(query) < 2:
                raise ValueError("query must have at least 2 characters")
            self.query = query or None
        if self.state is not None:
            state = str(self.state).strip().upper()
            if state and len(state) != 2:
                raise ValueError("state must be a two-letter UF code")
            self.state = state or None
        if self.blocked is not None and not isinstance(self.blocked, bool):
            raise ValueError("blocked must be a boolean")
        self.page = max(1, int(self.page or 1))
        self.page_size = min(100, max(1, int(self.page_size or 20)))
        self.sort_by = (self.sort_by or "supplier_name").strip().lower()
        if self.sort_by not in {
            "supplier_name",
            "supplier_code",
            "tax_id",
            "state",
        }:
            raise ValueError("invalid sort_by")
        self.sort_dir = (self.sort_dir or "asc").strip().lower()
        if self.sort_dir not in {"asc", "desc"}:
            raise ValueError("invalid sort_dir")

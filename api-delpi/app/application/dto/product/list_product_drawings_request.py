from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ListProductDrawingsRequest:
    code: str | None = None
    code_exact: bool = False
    filename: str | None = None
    revision: str | None = None
    file_kind: str | None = None
    has_variant: bool | None = None
    has_revision: bool | None = None
    modified_from: datetime | None = None
    modified_to: datetime | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    page: int = 1
    page_size: int = 50
    sort: str = "product_code"
    direction: str = "asc"

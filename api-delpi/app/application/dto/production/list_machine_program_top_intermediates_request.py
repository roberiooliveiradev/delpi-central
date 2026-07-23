from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListMachineProgramTopIntermediatesRequest:
    branch: str
    date_start: str | None = None
    date_end: str | None = None
    page: int = 1
    page_size: int = 10
    search: str | None = None

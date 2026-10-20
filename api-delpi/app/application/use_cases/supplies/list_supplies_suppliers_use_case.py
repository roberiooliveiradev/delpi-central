"""Use case — paginated supplier list/search (SA2010, company 01)."""

from __future__ import annotations

from typing import Any, Protocol

from app.application.dto.supplies.suppliers_request import SuppliersListRequest
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)


class SuppliersListRepositoryPort(Protocol):
    def search_suppliers_paged(
        self,
        *,
        query: str | None,
        state: str | None,
        blocked: bool | None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]: ...


class ListSuppliesSuppliersUseCase:
    def __init__(self, repository: SuppliersListRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SuppliersListRequest) -> dict[str, Any]:
        items, total = self._repository.search_suppliers_paged(
            query=request.query,
            state=request.state,
            blocked=request.blocked,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            page=request.page,
            page_size=request.page_size,
        )
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=items,
            extra={
                "query": request.query,
                "filters": {
                    "state": request.state,
                    "blocked": request.blocked,
                },
                "sort": {"by": request.sort_by, "dir": request.sort_dir},
                "scope": {"company": "01", "table": "SA2010"},
            },
        )

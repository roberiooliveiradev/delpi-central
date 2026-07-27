from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityListRepository(Protocol):
    def list_records(
        self,
        *,
        status: str | None = None,
        branch_code: str | None = None,
        sale_number: str | None = None,
        material_code: str | None = None,
        product_code: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]: ...


class ListLmpNonconformitiesUseCase:
    def __init__(self, repository: LmpNonconformityListRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        status: str | None = None,
        branch_code: str | None = None,
        sale_number: str | None = None,
        material_code: str | None = None,
        product_code: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        return self._repository.list_records(
            status=status,
            branch_code=branch_code,
            sale_number=sale_number,
            material_code=material_code,
            product_code=product_code,
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size,
        )

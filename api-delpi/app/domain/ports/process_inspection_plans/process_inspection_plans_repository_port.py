from __future__ import annotations

from typing import Protocol


class ProcessInspectionPlansRepositoryPort(Protocol):
    def get_summary(self, branch_scope: str) -> dict: ...

    def count_orders_without_plan(self, branch_scope: str) -> int: ...

    def list_orders_without_plan(
        self,
        branch_scope: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def count_products_without_plan(self, branch_scope: str) -> int: ...

    def list_products_without_plan(
        self,
        branch_scope: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def count_products_with_plan(self) -> int: ...

    def list_products_with_plan(
        self,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def product_has_plan(self, product_code: str) -> bool: ...

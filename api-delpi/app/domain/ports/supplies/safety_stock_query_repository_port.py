from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SafetyStockQueryRepositoryPort(ABC):
    @abstractmethod
    def fetch_filter_options(
        self,
        *,
        branch: str,
        include_blocked: bool,
    ) -> dict[str, list[str]]:
        ...

    @abstractmethod
    def fetch_summary(
        self,
        *,
        branch: str,
        include_blocked: bool,
        product_group: str | None,
        unit: str | None,
        search: str | None,
        status: str | None,
        include_without_safety_stock: bool,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        branch: str,
        include_blocked: bool,
        product_group: str | None,
        unit: str | None,
        search: str | None,
        status: str | None,
        include_without_safety_stock: bool,
    ) -> int:
        ...

    @abstractmethod
    def fetch_items(
        self,
        *,
        branch: str,
        include_blocked: bool,
        product_group: str | None,
        unit: str | None,
        search: str | None,
        status: str | None,
        include_without_safety_stock: bool,
        sort_by: str,
        sort_direction: str,
        offset: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_item_detail(
        self,
        *,
        branch: str,
        product_code: str,
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def fetch_open_purchase_orders(
        self,
        *,
        branch: str,
        product_code: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_open_commitments(
        self,
        *,
        branch: str,
        product_code: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_open_purchase_orders_for_branch(
        self,
        *,
        branch: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_open_commitments_for_branch(
        self,
        *,
        branch: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_materials_for_projection_batch(
        self,
        *,
        branch: str,
        include_blocked: bool,
        product_group: str | None,
        unit: str | None,
        search: str | None,
        include_without_safety_stock: bool,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_linked_suppliers(
        self,
        *,
        branch: str,
        product_code: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_consumption_analysis_rows(
        self,
        *,
        branch: str,
        period_start: str,
        include_blocked: bool,
        product_group: str | None,
        unit: str | None,
        search: str | None,
        product_code: str | None = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_consumption_monthly_series(
        self,
        *,
        branch: str,
        product_code: str,
        period_start: str,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def fetch_last_consumption_date(
        self,
        *,
        branch: str,
        product_code: str,
    ) -> str | None:
        ...

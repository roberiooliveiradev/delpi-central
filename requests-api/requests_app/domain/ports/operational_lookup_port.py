from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OperationalLookupPort(ABC):
    """TOTVS operational lookups for specialized request types (via adapters)."""

    @abstractmethod
    def search_parties(
        self,
        *,
        party_type: str,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def search_products(
        self,
        *,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def search_carriers(
        self,
        *,
        query: str,
        limit: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def list_open_sales_orders(
        self,
        *,
        branch: str,
        party_code: str,
        party_store: str,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def get_warehouse_01_balance(
        self,
        *,
        product_code: str,
        branch: str,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...

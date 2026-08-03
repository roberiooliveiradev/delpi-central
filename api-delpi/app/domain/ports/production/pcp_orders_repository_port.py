"""Port — ordens de produção."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PcpOrdersRepositoryPort(ABC):
    @abstractmethod
    def get_summary(self, **filters: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def count_items(self, **filters: Any) -> int:
        ...

    @abstractmethod
    def get_items(
        self,
        *,
        sort: str,
        offset: int,
        page_size: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_ranking(
        self,
        *,
        rank_by: str,
        metric: str,
        limit: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        ...

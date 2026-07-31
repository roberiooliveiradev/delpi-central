"""Port — horas improdutivas de produção."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class UnproductiveHoursRepositoryPort(ABC):
    @abstractmethod
    def get_summary(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_top_resource(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def get_top_operator(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def get_ranking(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        rank_by: str,
        metric: str,
        limit: int,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def count_items(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> int:
        ...

    @abstractmethod
    def get_items(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        sort: str,
        offset: int,
        page_size: int,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> list[dict[str, Any]]:
        ...

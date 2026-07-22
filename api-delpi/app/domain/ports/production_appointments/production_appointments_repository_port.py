from __future__ import annotations

from typing import Protocol


class ProductionAppointmentsRepositoryPort(Protocol):
    def list_work_centers(self, *, branch: str) -> list[dict]: ...

    def list_appointments(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        offset: int,
        page_size: int,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
    ) -> list[dict]: ...

    def count_appointments(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
    ) -> int: ...

    def get_summary_by_ct(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
    ) -> list[dict]: ...

    def get_summary_totals(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
    ) -> dict: ...

    def get_series(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        group_by: str = "day",
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
    ) -> list[dict]: ...

    def list_by_op(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        offset: int,
        page_size: int,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
    ) -> list[dict]: ...

    def count_by_op(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
    ) -> int: ...

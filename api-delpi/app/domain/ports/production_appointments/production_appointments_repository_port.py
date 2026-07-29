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
        mother_op: bool = False,
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
        mother_op: bool = False,
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
        mother_op: bool = False,
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
        mother_op: bool = False,
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
        mother_op: bool = False,
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
        mother_op: bool = False,
        op_family_prefix: str | None = None,
        child_ops_only: bool = False,
        exclude_op: str | None = None,
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
        mother_op: bool = False,
        op_family_prefix: str | None = None,
        child_ops_only: bool = False,
        exclude_op: str | None = None,
    ) -> int: ...

    def get_produced_totals(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
        product: str | None = None,
        products: list[str] | None = None,
        product_types: list[str] | None = None,
    ) -> dict: ...

    def list_produced_quantity(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
        product: str | None = None,
        products: list[str] | None = None,
        product_types: list[str] | None = None,
    ) -> list[dict]: ...

    def list_produced_detail(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
        product: str | None = None,
        products: list[str] | None = None,
        product_types: list[str] | None = None,
    ) -> list[dict]: ...

    def get_finished_ops_series(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        granularity: str = "day",
        product: str | None = None,
        mother_op: bool = False,
    ) -> list[dict]: ...

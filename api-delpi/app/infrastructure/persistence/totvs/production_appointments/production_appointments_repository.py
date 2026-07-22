from __future__ import annotations

import math

from app.domain.ports.production_appointments.production_appointments_repository_port import (
    ProductionAppointmentsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production_appointments.production_appointments_sql import (
    build_appointments_count_query,
    build_appointments_list_query,
    build_by_op_count_query,
    build_by_op_query,
    build_series_query,
    build_summary_by_ct_query,
    build_summary_totals_query,
    build_work_centers_catalog_query,
)


def calc_total_pages(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return int(math.ceil(total / page_size)) if total > 0 else 0


class ProductionAppointmentsRepository(BaseRepository, ProductionAppointmentsRepositoryPort):
    def list_work_centers(self, *, branch: str) -> list[dict]:
        query, params = build_work_centers_catalog_query(branch=branch)
        with self:
            return self.execute_query(query, params)

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
    ) -> list[dict]:
        query, params = build_appointments_list_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            offset=offset,
            page_size=page_size,
            work_center=work_center,
            op=op,
            product=product,
            search=search,
        )
        with self:
            return self.execute_query(query, params)

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
    ) -> int:
        query, params = build_appointments_count_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            work_center=work_center,
            op=op,
            product=product,
            search=search,
        )
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)

    def get_summary_by_ct(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
    ) -> list[dict]:
        query, params = build_summary_by_ct_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            work_center=work_center,
            op=op,
            product=product,
        )
        with self:
            return self.execute_query(query, params)

    def get_summary_totals(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
    ) -> dict:
        query, params = build_summary_totals_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            work_center=work_center,
            op=op,
            product=product,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

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
    ) -> list[dict]:
        query, params = build_series_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            group_by=group_by,
            work_center=work_center,
            op=op,
            product=product,
        )
        with self:
            return self.execute_query(query, params)

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
    ) -> list[dict]:
        query, params = build_by_op_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            offset=offset,
            page_size=page_size,
            work_center=work_center,
            op=op,
            product=product,
            search=search,
        )
        with self:
            return self.execute_query(query, params)

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
    ) -> int:
        query, params = build_by_op_count_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            work_center=work_center,
            op=op,
            product=product,
            search=search,
        )
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)

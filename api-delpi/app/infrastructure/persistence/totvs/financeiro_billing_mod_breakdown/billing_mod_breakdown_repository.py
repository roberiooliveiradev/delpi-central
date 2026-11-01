"""TOTVS repository for the R09 billing × MOD breakdown."""

from __future__ import annotations

from typing import Any

from app.domain.ports.financeiro_billing_mod_breakdown.billing_mod_breakdown_repository_port import (
    BillingModBreakdownRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from . import billing_mod_breakdown_sql

# SQL Server caps ~2100 parameters per statement; chunk the dynamic IN
# lists well below that bound so the set-based reads stay in a handful
# of round trips instead of hundreds of per-product calls.
_IN_CHUNK = 500


class BillingModBreakdownRepository(
    BaseRepository, BillingModBreakdownRepositoryPort
):
    def fetch_billed_quantities(
        self, *, period_start: str, period_end: str, branch: str
    ) -> list[dict[str, Any]]:
        sql, _ = billing_mod_breakdown_sql.billed_quantities_sql(
            branch=branch
        )
        params = billing_mod_breakdown_sql.billed_quantities_params(
            period_start=period_start,
            period_end=period_end,
            branch=branch,
        )
        with self:
            return self.execute_query(sql, tuple(params))

    def fetch_structure_edges(
        self, *, parent_codes: list[str], branch: str
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self:
            for chunk in _chunks(parent_codes):
                sql, params = billing_mod_breakdown_sql.structure_edges_sql(
                    parent_codes=chunk, branch=branch
                )
                rows.extend(self.execute_query(sql, tuple(params)))
        return rows

    def fetch_route_operations(
        self, *, product_codes: list[str], branch: str
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self:
            for chunk in _chunks(product_codes):
                sql, params = billing_mod_breakdown_sql.route_operations_sql(
                    product_codes=chunk, branch=branch
                )
                rows.extend(self.execute_query(sql, tuple(params)))
        return rows


def _chunks(codes: list[str], size: int = _IN_CHUNK):
    for start in range(0, len(codes), size):
        yield codes[start : start + size]

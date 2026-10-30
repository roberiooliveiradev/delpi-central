"""Repositório TOTVS da Auditoria de Consumo OP × operação (GLPI #1353).

Somente ``SELECT`` parametrizado — composição, classificação e aritmética
ficam no use case; este adaptador limita-se a trazer os fatos do Protheus.
"""

from __future__ import annotations

from typing import Sequence

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production_repositories import (
    consumption_audit_sql,
)


class ConsumptionAuditRepository(BaseRepository):
    """Leituras SC2/SD4/SD3/SH6/HZA/SH8/SG2/SG1/SB1 no grão da OP."""

    def fetch_order(
        self, *, production_order: str, branch: str
    ) -> dict | None:
        with self as repo:
            return repo.execute_one(
                consumption_audit_sql.order_sql(),
                (production_order, branch),
            )

    def fetch_family_orders(
        self,
        *,
        order_number: str,
        branch: str,
        exclude_production_order: str,
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.family_orders_sql(),
                (branch, order_number, exclude_production_order),
            )

    def fetch_commitments(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.commitments_sql(),
                (production_order, branch),
            )

    def fetch_movements(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.movements_sql(),
                (production_order, branch),
            )

    def fetch_appointments(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.appointments_sql(),
                (production_order, branch),
            )

    def fetch_operation_events(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.operation_events_sql(),
                (production_order, branch),
            )

    def fetch_allocations(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.allocations_sql(),
                (production_order, branch),
            )

    def fetch_routing(
        self, *, product_code: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.routing_sql(),
                (product_code, branch),
            )

    def fetch_bom_components(
        self, *, product_code: str, branch: str, reference_date: str
    ) -> list[dict]:
        # reference_date em AAAAMMDD — aparece duas vezes no filtro de
        # vigência (G1_INI <= ref e G1_FIM >= ref).
        params = (product_code, branch, reference_date, reference_date)
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.bom_components_sql(),
                params,
            )

    def fetch_product_metadata(
        self, *, codes: Sequence[str]
    ) -> dict[str, dict]:
        unique = sorted({str(c or "").strip() for c in codes if str(c or "").strip()})
        if not unique:
            return {}
        with self as repo:
            rows = repo.execute_query(
                consumption_audit_sql.product_metadata_sql(len(unique)),
                tuple(unique),
            )
        return {str(row.get("code") or "").strip(): row for row in rows}

    def fetch_parent_consumers(
        self, *, production_order: str, branch: str
    ) -> list[dict]:
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.parent_consumers_sql(),
                (production_order, branch),
            )

    def search_orders(
        self,
        *,
        branch: str,
        search: str | None = None,
        product: str | None = None,
        date_type: str = "emission",
        period_start: str | None = None,
        period_end: str | None = None,
        status: str | None = None,
        work_center: str | None = None,
        operation: str | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> list[dict]:
        where_sql, params = self._search_where(
            branch=branch,
            search=search,
            product=product,
            date_type=date_type,
            period_start=period_start,
            period_end=period_end,
            status=status,
            work_center=work_center,
            operation=operation,
        )
        with self as repo:
            return repo.execute_query(
                consumption_audit_sql.orders_search_sql(where_sql),
                params + (int(offset), int(limit)),
            )

    def count_orders(
        self,
        *,
        branch: str,
        search: str | None = None,
        product: str | None = None,
        date_type: str = "emission",
        period_start: str | None = None,
        period_end: str | None = None,
        status: str | None = None,
        work_center: str | None = None,
        operation: str | None = None,
    ) -> int:
        where_sql, params = self._search_where(
            branch=branch,
            search=search,
            product=product,
            date_type=date_type,
            period_start=period_start,
            period_end=period_end,
            status=status,
            work_center=work_center,
            operation=operation,
        )
        with self as repo:
            row = repo.execute_one(
                consumption_audit_sql.orders_search_count_sql(where_sql),
                params,
            )
        return int(row.get("total") or 0) if row else 0

    @staticmethod
    def _search_where(
        *,
        branch: str,
        search: str | None,
        product: str | None,
        date_type: str,
        period_start: str | None,
        period_end: str | None,
        status: str | None,
        work_center: str | None,
        operation: str | None,
    ) -> tuple[str, tuple]:
        return consumption_audit_sql.orders_search_where(
            branch=branch,
            search=search,
            product=product,
            date_type=date_type,
            period_start=period_start,
            period_end=period_end,
            status=status,
            work_center=work_center,
            operation=operation,
        )

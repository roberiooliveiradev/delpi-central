"""TOTVS repository for the R10 cost-center-expenses engine (doc 126).

Row fetch only: the SQL in ``cost_center_expenses_sql`` scopes the
in-competence SD1 lines for the authorized branches; universe split,
exclusion reasons and findings are computed by the use case.
"""

from __future__ import annotations

from typing import Any

from app.domain.ports.financeiro_cost_center_expenses.cost_center_expenses_repository_port import (
    CostCenterExpensesRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import (
    BaseRepository,
)
from app.infrastructure.persistence.totvs.financeiro_cost_center_expenses import (
    cost_center_expenses_sql,
)


class CostCenterExpensesRepository(
    BaseRepository, CostCenterExpensesRepositoryPort
):
    def fetch_lines(
        self,
        *,
        period_start: str,
        period_end: str,
        branches: tuple[str, ...],
        cost_center: str | None,
        product_code: str | None,
        document: str | None,
        supplier_code: str | None,
        tes: str | None,
    ) -> list[dict[str, Any]]:
        sql, params = cost_center_expenses_sql.build_lines_query(
            period_start=period_start,
            period_end=period_end,
            branches=branches,
            cost_center=cost_center,
            product_code=product_code,
            document=document,
            supplier_code=supplier_code,
            tes=tes,
        )
        with self as repo:
            return repo.execute_query(sql, tuple(params)) or []

"""TOTVS repository for the R11 billing-exclusion roster (doc 126).

Row fetch only: the SQL in ``billing_exclusion_roster_sql`` scopes the
in-competence SD2 population related to the roster criteria; candidates
classification, sibling evaluation and findings are computed by the use
case.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_billing_exclusion_roster.constantes import (
    ROSTER_PRODUCT_GROUP,
    ROSTER_TES,
)
from app.domain.ports.financeiro_billing_exclusion_roster.billing_exclusion_roster_repository_port import (
    BillingExclusionRosterRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import (
    BaseRepository,
)
from app.infrastructure.persistence.totvs.financeiro_billing_exclusion_roster import (
    billing_exclusion_roster_sql,
)


class BillingExclusionRosterRepository(
    BaseRepository, BillingExclusionRosterRepositoryPort
):
    def fetch_lines(
        self,
        *,
        period_start: str,
        period_end: str,
        branches: tuple[str, ...],
        product_group: str | None,
        product_code: str | None,
        document: str | None,
        customer_code: str | None,
        tes: str | None,
        roster_product_group: str = ROSTER_PRODUCT_GROUP,
        roster_tes: str = ROSTER_TES,
    ) -> list[dict[str, Any]]:
        sql, params = billing_exclusion_roster_sql.build_lines_query(
            period_start=period_start,
            period_end=period_end,
            branches=branches,
            roster_product_group=roster_product_group,
            roster_tes=roster_tes,
            product_group=product_group,
            product_code=product_code,
            document=document,
            customer_code=customer_code,
            tes=tes,
        )
        with self as repo:
            return repo.execute_query(sql, tuple(params)) or []

from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)
from app.domain.ports.financial.purchase_freight_repository_port import (
    PurchaseFreightRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.financial_repositories.purchase_freight_sql import (
    build_purchase_freight_branch_filter,
    build_purchase_freight_links_params,
    build_purchase_freight_links_sql,
    build_purchase_freight_scope_filter,
)


class PurchaseFreightRepository(BaseRepository, PurchaseFreightRepositoryPort):

    def list_purchase_freight_links(
        self,
        request: PurchaseFreightLinksRequest,
        *,
        limit: int,
    ) -> list[dict]:
        branch_clause, branch_params = build_purchase_freight_branch_filter(
            request.branch
        )
        scope_clause, scope_params = build_purchase_freight_scope_filter(
            issue_start=request.issue_start,
            issue_end=request.issue_end,
            entry_start=request.entry_start,
            entry_end=request.entry_end,
            supplier=request.supplier,
            invoice_document=request.invoice_document,
            freight_document=request.freight_document,
        )
        sql = build_purchase_freight_links_sql(
            branch_clause=branch_clause,
            scope_clause=scope_clause,
        )
        params = build_purchase_freight_links_params(
            branch_params=branch_params,
            scope_params=scope_params,
            fetch_limit=max(1, int(limit)) + 1,
        )

        with self:
            return self.execute_query(sql, params)

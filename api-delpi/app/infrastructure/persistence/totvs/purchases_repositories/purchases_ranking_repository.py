from app.domain.services.production.purchase_validity_filter_service import (
    PurchaseValidityFilterService,
)
from app.domain.ports.purchases.purchases_ranking_repository_port import (
    PurchasesRankingRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class PurchasesRankingRepository(
    BaseRepository,
    PurchasesRankingRepositoryPort,
):
    def fetch_top_products(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        limit: int,
    ) -> list[dict]:
        branch_filter = "AND SD1.D1_FILIAL = ?" if branch else ""
        params: list = [
            date_start,
            date_end_exclusive,
            *PurchaseValidityFilterService.supplier_filter_params(),
        ]
        if branch:
            params.append(branch)

        sql = f"""
        SELECT TOP {int(limit)}
            SD1.D1_FILIAL AS branch,
            SD1.D1_COD AS product_code,
            SB1.B1_DESC AS description,
            COUNT(DISTINCT SD1.D1_DOC) AS invoice_count,
            SUM(SD1.D1_QUANT) AS total_quantity,
            SUM(SD1.D1_TOTAL) AS total_value,
            MAX(SD1.D1_EMISSAO) AS last_purchase_date
        FROM SD1010 SD1 WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = SD1.D1_COD
           AND SB1.D_E_L_E_T_ = ''
        {PurchaseValidityFilterService.supplier_join_sql()}
        WHERE SD1.D_E_L_E_T_ = ''
          AND SD1.D1_EMISSAO >= ?
          AND SD1.D1_EMISSAO < ?
          {PurchaseValidityFilterService.supplier_filter_sql()}
          {branch_filter}
        GROUP BY
            SD1.D1_FILIAL,
            SD1.D1_COD,
            SB1.B1_DESC
        ORDER BY
            total_quantity DESC,
            total_value DESC,
            SD1.D1_COD ASC
        """

        with self as repo:
            return repo.execute_query(sql, tuple(params))

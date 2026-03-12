# app/infrastructure/persistence/totvs/product_repositories/product_stock_repository.py
from typing import Optional, Tuple, List

from app.infrastructure.persistence.base_repository import BaseRepository
from app.infrastructure.persistence.pagination import paginate
from app.infrastructure.persistence.query_builder import QueryBuilder

from app.domain.entities.stock import Stock
from app.domain.ports.product_stock_repository_port import ProductStockRepositoryPort


class ProductStockRepository(
    BaseRepository,
    ProductStockRepositoryPort
):

    def list_stock(
        self,
        code: str,
        page: int,
        page_size: int,
        branch: Optional[str],
        location: Optional[str]
    ) -> Tuple[int, List[Stock]]:

        paging = paginate(page, page_size)

        qb = QueryBuilder()

        qb.raw("SB2.D_E_L_E_T_ = ''")
        qb.eq("SB2.B2_COD", code)
        qb.eq("SB2.B2_FILIAL", branch)
        qb.eq("SB2.B2_LOCAL", location)

        where_clause, params = qb.build()

        # ---------------------------
        # COUNT
        # ---------------------------

        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM SB2010 SB2
        WHERE {where_clause}
        """

        # ---------------------------
        # DATA
        # ---------------------------

        data_sql = f"""
        SELECT
            SB2.B2_COD      AS product_code,
            SB2.B2_FILIAL   AS branch,
            SB2.B2_LOCAL    AS warehouse,

            SB2.B2_QATU     AS current_quantity,
            SB2.B2_QEMP     AS committed_quantity,
            SB2.B2_RESERVA  AS reserved_quantity,

            (SB2.B2_QATU - SB2.B2_QEMP - SB2.B2_RESERVA) AS available_quantity,

            SBZ.BZ_MPLOCAL  AS physical_location,
            SBZ.BZ_LOCPAD   AS default_warehouse,
            SBZ.BZ_CUSTO    AS cost_center,
            SBZ.BZ_GALPAO   AS warehouse_section

        FROM SB2010 SB2

        LEFT JOIN SBZ010 SBZ
            ON SBZ.BZ_COD = SB2.B2_COD
            AND SBZ.BZ_FILIAL = SB2.B2_FILIAL

        WHERE {where_clause}

        ORDER BY
            SB2.B2_FILIAL,
            SB2.B2_LOCAL

        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                params
            )

            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                data_sql,
                params + (paging["offset"], paging["page_size"])
            )

        items = [
            Stock(**r)
            for r in rows
        ]

        return total, items
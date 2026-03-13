# app/infrastructure/persistence/totvs/product_repositories/product_internal_movements_repository.py

from typing import Optional

from app.infrastructure.persistence.base_repository import BaseRepository
from app.infrastructure.persistence.pagination import paginate
from app.infrastructure.persistence.query_builder import QueryBuilder

from app.application.models.page import Page
from app.domain.entities.product.internal_movement import InternalMovement
from app.domain.ports.product.product_internal_movements_repository_port import ProductInternalMovementsRepositoryPort


class ProductInternalMovementsRepository(
    BaseRepository,
    ProductInternalMovementsRepositoryPort
):

    def list_internal_movements(
        self,
        code: str,
        page: int,
        page_size: int,
        date_start: Optional[str],
        date_end: Optional[str],
        branch: Optional[str],
        location: Optional[str],
        tm: Optional[str],
        op: Optional[str],
    ) -> Page[InternalMovement]:

        paging = paginate(page, page_size)

        qb = QueryBuilder()

        qb.raw("SD3.D_E_L_E_T_ = ''")
        qb.eq("SD3.D3_COD", code)

        qb.date_range("SD3.D3_EMISSAO", date_start, date_end)

        qb.eq("SD3.D3_FILIAL", branch)
        qb.eq("SD3.D3_LOCAL", location)
        qb.eq("SD3.D3_TM", tm)
        qb.eq("SD3.D3_OP", op)

        where_clause, params = qb.build()

        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM SD3010 SD3
        WHERE {where_clause}
        """

        data_sql = f"""
        SELECT
            SD3.D3_FILIAL   AS branch,
            SD3.D3_LOCAL    AS location,
            SD3.D3_DOC      AS document,
            SD3.D3_EMISSAO  AS issue_date,

            SD3.D3_COD      AS product_code,
            SB1.B1_DESC     AS product_description,
            SB1.B1_UM       AS unit,

            SD3.D3_TM       AS movement_type,
            SD3.D3_CF       AS cf,
            SD3.D3_QUANT    AS quantity,
            SD3.D3_OP       AS production_order,
            SD3.D3_USUARIO  AS user_name

        FROM SD3010 SD3

        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = SD3.D3_COD
            AND SB1.D_E_L_E_T_ = ''

        WHERE {where_clause}

        ORDER BY
            SD3.D3_EMISSAO DESC,
            SD3.R_E_C_N_O_ DESC

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
            InternalMovement(**r)
            for r in rows
        ]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
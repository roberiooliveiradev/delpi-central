# app/infrastructure/persistence/totvs/product_repositories/product_purchases_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository
from app.infrastructure.persistence.pagination import paginate

from app.application.models.page import Page
from app.domain.entities.purchase import Purchase
from app.domain.ports.product_purchases_repository_port import ProductPurchasesRepositoryPort


class ProductPurchasesRepository(
    BaseRepository,
    ProductPurchasesRepositoryPort
):

    def list_purchases(
        self,
        code: str,
        page: int,
        page_size: int
    ) -> Page[Purchase]:

        paging = paginate(page, page_size)

        count_sql = """
        SELECT COUNT(DISTINCT C7.C7_NUM) AS total
        FROM SC7010 C7
        WHERE C7.D_E_L_E_T_ = ''
        AND C7.C7_PRODUTO = ?
        """

        data_sql = """
        SELECT
            C7.C7_NUM        AS order_number,
            C7.C7_FILIAL     AS branch,
            C7.C7_EMISSAO    AS issue_date,

            C7.C7_FORNECE    AS supplier_code,
            C7.C7_LOJA       AS store,
            SA2.A2_NOME      AS supplier_name,

            C7.C7_PRODUTO    AS product_code,

            SUM(C7.C7_QUANT) AS ordered_quantity,
            AVG(C7.C7_PRECO) AS unit_price

        FROM SC7010 C7

        LEFT JOIN SA2010 SA2
            ON SA2.A2_COD = C7.C7_FORNECE
            AND SA2.A2_LOJA = C7.C7_LOJA
            AND SA2.D_E_L_E_T_ = ''

        WHERE
            C7.D_E_L_E_T_ = ''
            AND C7.C7_PRODUTO = ?

        GROUP BY
            C7.C7_NUM,
            C7.C7_FILIAL,
            C7.C7_EMISSAO,
            C7.C7_FORNECE,
            C7.C7_LOJA,
            SA2.A2_NOME,
            C7.C7_PRODUTO

        ORDER BY C7.C7_EMISSAO DESC

        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                (code,)
            )

            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                data_sql,
                (code, paging["offset"], paging["page_size"])
            )

        items = [
            Purchase(**r)
            for r in rows
        ]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
# app/infrastructure/persistence/totvs/product_repositories/product_customers_repository.py

from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.ports.product_customers_repository_port import ProductCustomersRepositoryPort
from app.domain.entities.customer import Customer
from app.application.models.page import Page
from app.infrastructure.persistence.pagination import paginate


class ProductCustomersRepository(BaseRepository, ProductCustomersRepositoryPort):

    def list_customers(self, code: str, page: int, page_size: int) -> Page[Customer]:

        paging = paginate(page, page_size)

        count_sql = """
            SELECT COUNT(*) AS total
            FROM SA7010
            WHERE D_E_L_E_T_ = ''
            AND A7_PRODUTO = ?
        """

        sql = """
            WITH last_sale AS (
                SELECT
                    SD2.D2_COD          AS product_code,
                    SD2.D2_CLIENTE      AS customer_code,
                    SD2.D2_LOJA         AS store,
                    MAX(SD2.D2_EMISSAO) AS last_sale_date,
                    SUM(SD2.D2_QUANT)   AS total_quantity,
                    AVG(SD2.D2_PRCVEN)  AS average_price
                FROM SD2010 SD2
                WHERE SD2.D_E_L_E_T_ = ''
                AND SD2.D2_COD = ?
                GROUP BY
                    SD2.D2_COD,
                    SD2.D2_CLIENTE,
                    SD2.D2_LOJA
            )

            SELECT
                SB1.B1_COD,
                SB1.B1_DESC,
                SB1.B1_UM,

                SA1.A1_COD,
                SA1.A1_LOJA,
                SA1.A1_NOME,
                SA1.A1_MSBLQL,

                SA7.A7_CODCLI,
                SA7.A7_DESCCLI,

                SA7.A7_PRECO01,
                SA7.A7_DTREF01,

                LS.average_price,
                LS.last_sale_date,
                LS.total_quantity

            FROM SA7010 SA7

            INNER JOIN SA1010 SA1
                ON SA1.A1_COD = SA7.A7_CLIENTE
                AND SA1.A1_LOJA = SA7.A7_LOJA
                AND SA1.D_E_L_E_T_ = ''

            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SA7.A7_PRODUTO
                AND SB1.D_E_L_E_T_ = ''

            LEFT JOIN last_sale LS
                ON LS.product_code = SA7.A7_PRODUTO
                AND LS.customer_code = SA7.A7_CLIENTE
                AND LS.store = SA7.A7_LOJA

            WHERE
                SA7.D_E_L_E_T_ = ''
                AND SA7.A7_PRODUTO = ?

            ORDER BY SA1.A1_NOME
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                (code,)
            )

            total = int(total_row["total"]) if total_row else 0

            rows = repo.execute_query(
                sql,
                (
                    code,
                    code,
                    paging["offset"],
                    paging["page_size"]
                )
            )

        customers = [
            Customer(
                product_code=r["B1_COD"],
                product_description=r["B1_DESC"],
                unit=r["B1_UM"],

                customer_code=r["A1_COD"],
                store=r["A1_LOJA"],
                customer_name=r["A1_NOME"],
                blocked=r["A1_MSBLQL"],

                customer_product_code=r["A7_CODCLI"],
                customer_product_description=r["A7_DESCCLI"],

                registered_price=r["A7_PRECO01"],
                registered_price_date=r["A7_DTREF01"],

                last_sale_price=r["average_price"],
                last_sale_date=r["last_sale_date"],
                total_quantity=r["total_quantity"]
            )
            for r in rows
        ]

        return Page(
            items=customers,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"]
        )
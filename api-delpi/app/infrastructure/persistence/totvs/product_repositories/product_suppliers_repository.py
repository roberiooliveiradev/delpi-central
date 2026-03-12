# app/infrastructure/persistence/totvs/product_repositories/product_suppliers_repository.py

from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.ports.product_suppliers_repository_port import ProductSuppliersRepositoryPort
from app.application.models.page import Page
from app.domain.entities.supplier import Supplier
from app.infrastructure.persistence.pagination import paginate


class ProductSuppliersRepository(BaseRepository, ProductSuppliersRepositoryPort):

    def list_suppliers(self, code: str, page: int, page_size: int) -> Page[Supplier]:

        paging = paginate(page, page_size)

        count_sql = """
        SELECT COUNT(*) AS total
        FROM SA5010
        WHERE D_E_L_E_T_ = ''
        AND A5_PRODUTO = ?
        """

        with self as repo:

            total_row = repo.execute_one(
                count_sql,
                (code,)
            )

            total = int(total_row["total"]) if total_row else 0

            sql = """
            WITH LAST_PURCHASE AS (
                SELECT
                    C7.C7_PRODUTO   AS product_code,
                    C7.C7_FORNECE   AS supplier_code,
                    C7.C7_LOJA      AS supplier_store,
                    C7.C7_PRECO     AS last_price,
                    C7.C7_EMISSAO   AS last_price_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            C7.C7_PRODUTO,
                            C7.C7_FORNECE,
                            C7.C7_LOJA
                        ORDER BY
                            C7.C7_EMISSAO DESC
                    ) AS rn
                FROM SC7010 C7
                WHERE
                    C7.D_E_L_E_T_ = ''
                    AND C7.C7_PRODUTO = ?
            ),

            REAL_LEAD_TIME AS (
                SELECT
                    C7.C7_PRODUTO   AS product_code,
                    C7.C7_FORNECE   AS supplier_code,
                    C7.C7_LOJA      AS supplier_store,
                    COUNT(*)        AS sample_size,
                    AVG(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS avg_lead_time_days,
                    MIN(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS min_lead_time_days,
                    MAX(DATEDIFF(DAY, C7.C7_EMISSAO, SD1.D1_EMISSAO)) AS max_lead_time_days
                FROM SC7010 C7
                INNER JOIN SD1010 SD1
                    ON SD1.D1_PEDIDO  = C7.C7_NUM
                    AND SD1.D1_FORNECE = C7.C7_FORNECE
                    AND SD1.D1_LOJA    = C7.C7_LOJA
                    AND SD1.D1_COD     = C7.C7_PRODUTO
                    AND SD1.D_E_L_E_T_ = ''
                WHERE
                    C7.D_E_L_E_T_ = ''
                    AND C7.C7_PRODUTO = ?
                GROUP BY
                    C7.C7_PRODUTO,
                    C7.C7_FORNECE,
                    C7.C7_LOJA
            )

            SELECT
                -- Product
                SB1.B1_COD      AS product_code,
                SB1.B1_DESC     AS product_description,
                SB1.B1_UM       AS unit,

                -- Supplier
                SA5.A5_FORNECE  AS supplier_code,
                SA5.A5_LOJA     AS supplier_store,
                SA2.A2_NOME     AS supplier_name,

                -- Supplier product codes
                SA5.A5_CODPRF   AS supplier_part_number,
                SA5.A5_CODPRCA  AS catalog_code,
                SA5.A5_CODBAR   AS barcode,

                -- Lead times
                SA5.A5_LEAD_T           AS registered_lead_time_days,
                RLT.avg_lead_time_days  AS real_avg_lead_time_days,
                RLT.min_lead_time_days  AS real_min_lead_time_days,
                RLT.max_lead_time_days  AS real_max_lead_time_days,
                RLT.sample_size         AS real_lead_time_sample_size,

                -- Last price
                LP.last_price           AS last_price,
                LP.last_price_date      AS last_price_date

            FROM SA5010 SA5

            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = SA5.A5_PRODUTO
                AND SB1.D_E_L_E_T_ = ''

            LEFT JOIN SA2010 SA2
                ON SA2.A2_COD = SA5.A5_FORNECE
                AND SA2.A2_LOJA = SA5.A5_LOJA
                AND SA2.D_E_L_E_T_ = ''

            LEFT JOIN LAST_PURCHASE LP
                ON LP.product_code = SA5.A5_PRODUTO
                AND LP.supplier_code = SA5.A5_FORNECE
                AND LP.supplier_store = SA5.A5_LOJA
                AND LP.rn = 1

            LEFT JOIN REAL_LEAD_TIME RLT
                ON RLT.product_code = SA5.A5_PRODUTO
                AND RLT.supplier_code = SA5.A5_FORNECE
                AND RLT.supplier_store = SA5.A5_LOJA

            WHERE
                SA5.D_E_L_E_T_ = ''
                AND SA5.A5_PRODUTO = ?

            ORDER BY SA5.A5_FORNECE
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """

            rows = repo.execute_query(
                sql,
                (
                    code,
                    code,
                    code,
                    paging["offset"],
                    paging["page_size"]
                )
            )

        suppliers = [
            Supplier(
                product_code=r["product_code"],
                product_description=r["product_description"],
                unit=r["unit"],

                supplier_code=r["supplier_code"],
                supplier_store=r["supplier_store"],
                supplier_name=r["supplier_name"],

                supplier_part_number=r["supplier_part_number"],
                catalog_code=r["catalog_code"],
                barcode=r["barcode"],

                registered_lead_time_days=r["registered_lead_time_days"],
                real_avg_lead_time_days=r["real_avg_lead_time_days"],
                real_min_lead_time_days=r["real_min_lead_time_days"],
                real_max_lead_time_days=r["real_max_lead_time_days"],
                real_lead_time_sample_size=r["real_lead_time_sample_size"],

                last_price=r["last_price"],
                last_price_date=r["last_price_date"],
            )
            for r in rows
        ]

        return Page(
            items=suppliers,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"]
        )
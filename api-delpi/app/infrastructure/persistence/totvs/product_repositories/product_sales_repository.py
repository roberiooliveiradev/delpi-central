# app/infrastructure/persistence/totvs/product_repositories/product_sales_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository

from app.domain.entities.product.product_sales_summary import ProductSalesSummary
from app.domain.ports.product.product_sales_repository_port import ProductSalesRepositoryPort


class ProductSalesRepository(
    BaseRepository,
    ProductSalesRepositoryPort
):

    def get_sales_summary(
        self,
        code: str
    ) -> ProductSalesSummary:

        product_sql = """
        SELECT
            B1_COD  AS product_code,
            B1_DESC AS product_description,
            B1_UM   AS unit
        FROM SB1010
        WHERE D_E_L_E_T_ = ''
        AND B1_COD = ?
        """

        sales_sql = """
        SELECT
            SUM(D2_QUANT)          AS total_quantity,
            SUM(D2_TOTAL)          AS total_value,
            AVG(D2_PRCVEN)         AS average_price,
            COUNT(DISTINCT D2_DOC) AS documents,
            MIN(D2_EMISSAO)        AS first_sale_date,
            MAX(D2_EMISSAO)        AS last_sale_date
        FROM SD2010
        WHERE D_E_L_E_T_ = ''
        AND D2_COD = ?
        """

        with self as repo:

            product = repo.execute_one(product_sql, (code,))
            summary = repo.execute_one(sales_sql, (code,))

        return ProductSalesSummary(
            product_code=code,
            product_description=product["product_description"] if product else None,
            unit=product["unit"] if product else None,

            total_quantity=float(summary["total_quantity"] or 0),
            total_value=float(summary["total_value"] or 0),
            average_price=float(summary["average_price"] or 0),

            documents=int(summary["documents"] or 0),

            first_sale_date=summary["first_sale_date"],
            last_sale_date=summary["last_sale_date"]
        )
# app/infrastructure/persistence/totvs/product_repositories/product_sales_billing_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository

from app.domain.entities.product.product_sales_billing import ProductSalesBilling
from app.domain.ports.product.product_sales_billing_repository_port import ProductSalesBillingRepositoryPort


class ProductSalesBillingRepository(
    BaseRepository,
    ProductSalesBillingRepositoryPort
):

    def get_sales_billing(
        self,
        code: str
    ) -> ProductSalesBilling:

        sql = """
        SELECT
            SUM(D2_TOTAL)          AS billed_value,
            COUNT(DISTINCT D2_DOC) AS documents,
            MIN(D2_EMISSAO)        AS first_billing_date,
            MAX(D2_EMISSAO)        AS last_billing_date
        FROM SD2010
        WHERE D_E_L_E_T_ = ''
        AND D2_COD = ?
        """

        with self as repo:

            row = repo.execute_one(sql, (code,))

        return ProductSalesBilling(
            value=float(row["billed_value"] or 0),
            documents=int(row["documents"] or 0),
            first_billing_date=row["first_billing_date"],
            last_billing_date=row["last_billing_date"]
        )
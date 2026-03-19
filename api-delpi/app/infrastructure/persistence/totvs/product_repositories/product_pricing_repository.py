# app/infrastructure/persistence/totvs/product_repositories/product_pricing_repository.py
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from app.domain.entities.product.product_pricing import (
    ProductPricing,
    ProductPricingItem
)
from app.domain.ports.product.product_pricing_repository_port import ProductPricingRepositoryPort


class ProductPricingRepository(
    BaseRepository,
    ProductPricingRepositoryPort
):

    def get_product_pricing(
        self,
        code: str
    ) -> ProductPricing | None:

        product_sql = """
        SELECT
            B1_COD  AS product_code,
            B1_DESC AS product_description,
            B1_UM   AS unit
        FROM SB1010
        WHERE D_E_L_E_T_ = ''
        AND B1_COD = ?
        """

        pricing_sql = """
        SELECT
            DA1.DA1_CODTAB AS table_code,
            DA0.DA0_DESCRI AS table_description,

            DA1.DA1_PRCVEN AS sale_price,
            DA1.DA1_PRCMAX AS max_price,

            DA1.DA1_VLRDES AS discount_value,
            DA1.DA1_PERDES AS discount_percent,

            DA1.DA1_QTDLOT AS lot_quantity,
            DA1.DA1_ESTADO AS state,
            DA1.DA1_TPOPER AS operation_type,
            DA1.DA1_MOEDA  AS currency,

            DA1.DA1_DATVIG AS valid_from,
            DA1.DA1_ATIVO  AS active

        FROM DA1010 DA1

        INNER JOIN DA0010 DA0
            ON DA0.DA0_FILIAL = DA1.DA1_FILIAL
            AND DA0.DA0_CODTAB = DA1.DA1_CODTAB
            AND DA0.D_E_L_E_T_ = ''

        WHERE DA1.D_E_L_E_T_ = ''
        AND DA1.DA1_CODPRO = ?

        ORDER BY DA1.DA1_CODTAB, DA1.DA1_DATVIG DESC
        """

        with self as repo:

            product = repo.execute_one(product_sql, (code,))

            if not product:
                return None

            rows = repo.execute_query(pricing_sql, (code,))

        prices = [
            ProductPricingItem(
                table_code=r["table_code"],
                table_description=r["table_description"],
                sale_price=float(r["sale_price"] or 0),
                max_price=float(r["max_price"] or 0),
                discount_value=float(r["discount_value"] or 0),
                discount_percent=float(r["discount_percent"] or 0),
                lot_quantity=float(r["lot_quantity"] or 0),
                state=r["state"],
                operation_type=r["operation_type"],
                currency=r["currency"],
                valid_from=r["valid_from"],
                active=r["active"],
            )
            for r in rows
        ]

        return ProductPricing(
            product_code=product["product_code"],
            product_description=product["product_description"],
            unit=product["unit"],
            prices=prices
        )
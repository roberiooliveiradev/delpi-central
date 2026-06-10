from app.domain.ports.product.product_raw_material_price_repository_port import (
    ProductRawMaterialPriceRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_INTERNAL_SUPPLIERS = ("000019", "001149")


class ProductRawMaterialPriceRepository(
    BaseRepository,
    ProductRawMaterialPriceRepositoryPort,
):

    def fetch_product_header(self, code: str) -> dict | None:
        sql = """
        SELECT TOP 1
            B1_COD  AS product_code,
            B1_DESC AS description,
            B1_TIPO AS product_type,
            B1_UM   AS unit,
            B1_GRUPO AS group_code,
            B1_UPRC AS registered_last_purchase_price,
            B1_UCOM AS registered_last_purchase_date,
            B1_PICM AS registered_icms_rate,
            B1_CUSTD AS standard_cost
        FROM SB1010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND B1_COD = ?
        """
        with self as repo:
            return repo.execute_one(sql, (code,))

    def fetch_last_purchase(
        self,
        code: str,
        branch: str | None = None,
    ) -> dict | None:
        branch_filter = "AND SD1.D1_FILIAL = ?" if branch else ""
        params: list = [code, *_INTERNAL_SUPPLIERS]
        if branch:
            params.append(branch)

        sql = f"""
        WITH ULTIMA_NF AS (
            SELECT
                SD1.D1_FILIAL AS branch,
                SD1.D1_COD AS product_code,
                SD1.D1_DOC AS invoice_number,
                SD1.D1_SERIE AS invoice_series,
                SD1.D1_EMISSAO AS issue_date,
                SD1.D1_DTDIGIT AS entry_date,
                SD1.D1_FORNECE AS supplier_code,
                SD1.D1_LOJA AS supplier_store,
                SD1.D1_QUANT AS quantity,
                SD1.D1_VUNIT AS unit_price,
                SD1.D1_TOTAL AS total_value,
                SD1.D1_VALICM AS icms_value,
                SD1.D1_PICM AS icms_rate,
                SD1.D1_PEDIDO AS purchase_order,
                SA2.A2_NOME AS supplier_name,
                SA2.A2_CGC AS supplier_tax_id,
                SA2.A2_EST AS supplier_state,
                A5.A5_CODPRF AS supplier_part_number,
                ROW_NUMBER() OVER (
                    ORDER BY
                        SD1.D1_EMISSAO DESC,
                        SD1.D1_DTDIGIT DESC,
                        SD1.D1_DOC DESC
                ) AS rn
            FROM SD1010 SD1 WITH (NOLOCK)
            INNER JOIN SA2010 SA2 WITH (NOLOCK)
                ON SA2.A2_COD = SD1.D1_FORNECE
               AND SA2.A2_LOJA = SD1.D1_LOJA
               AND SA2.D_E_L_E_T_ = ''
            LEFT JOIN SA5010 A5 WITH (NOLOCK)
                ON A5.A5_PRODUTO = SD1.D1_COD
               AND A5.A5_FORNECE = SD1.D1_FORNECE
               AND A5.A5_LOJA = SD1.D1_LOJA
               AND A5.D_E_L_E_T_ = ''
            WHERE SD1.D_E_L_E_T_ = ''
              AND SD1.D1_COD = ?
              AND SD1.D1_FORNECE NOT IN (?, ?)
              AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
              {branch_filter}
        )
        SELECT
            branch,
            product_code,
            invoice_number,
            invoice_series,
            issue_date,
            entry_date,
            supplier_code,
            supplier_store,
            quantity,
            unit_price,
            total_value,
            icms_value,
            icms_rate,
            purchase_order,
            supplier_name,
            supplier_tax_id,
            supplier_state,
            supplier_part_number
        FROM ULTIMA_NF
        WHERE rn = 1
        """
        with self as repo:
            return repo.execute_one(sql, tuple(params))

    def fetch_purchase_price_history(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
        limit: int = 24,
    ) -> list[dict]:
        branch_filter = "AND SD1.D1_FILIAL = ?" if branch else ""
        params: list = [limit, code, date_start, date_end_exclusive, *_INTERNAL_SUPPLIERS]
        if branch:
            params.append(branch)

        sql = f"""
        SELECT TOP (?)
            SD1.D1_FILIAL AS branch,
            SD1.D1_EMISSAO AS issue_date,
            SD1.D1_DTDIGIT AS entry_date,
            SD1.D1_DOC AS invoice_number,
            SD1.D1_SERIE AS invoice_series,
            SD1.D1_FORNECE AS supplier_code,
            SD1.D1_LOJA AS supplier_store,
            SA2.A2_NOME AS supplier_name,
            SD1.D1_VUNIT AS unit_price,
            SD1.D1_VALICM AS icms_value,
            SD1.D1_PICM AS icms_rate,
            SD1.D1_QUANT AS quantity,
            SD1.D1_TOTAL AS total_value,
            SD1.D1_PEDIDO AS purchase_order
        FROM SD1010 SD1 WITH (NOLOCK)
        INNER JOIN SA2010 SA2 WITH (NOLOCK)
            ON SA2.A2_COD = SD1.D1_FORNECE
           AND SA2.A2_LOJA = SD1.D1_LOJA
           AND SA2.D_E_L_E_T_ = ''
        WHERE SD1.D_E_L_E_T_ = ''
          AND SD1.D1_COD = ?
          AND SD1.D1_EMISSAO >= ?
          AND SD1.D1_EMISSAO < ?
          AND SD1.D1_FORNECE NOT IN (?, ?)
          AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
          {branch_filter}
        ORDER BY
            SD1.D1_EMISSAO DESC,
            SD1.D1_DTDIGIT DESC,
            SD1.D1_DOC DESC
        """
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))

    def fetch_purchase_budget_history(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        branch_filter_sc = "AND C1.C1_FILIAL = ?" if branch else ""
        branch_filter_pc = "AND C7.C7_FILIAL = ?" if branch else ""
        params: list = [code, date_start, date_end_exclusive]
        if branch:
            params.append(branch)
        params.extend([code, date_start, date_end_exclusive])
        if branch:
            params.append(branch)

        sql = f"""
        WITH REQUISICOES AS (
            SELECT
                'SC1010' AS source,
                C1.C1_FILIAL AS branch,
                C1.C1_NUM AS document_number,
                C1.C1_ITEM AS item,
                C1.C1_EMISSAO AS issue_date,
                C1.C1_DATPRF AS required_date,
                C1.C1_FORNECE AS supplier_code,
                C1.C1_LOJA AS supplier_store,
                SA2.A2_NOME AS supplier_name,
                C1.C1_QUANT AS quantity,
                C1.C1_PRECO AS unit_price,
                C1.C1_TOTAL AS total_value,
                C1.C1_PEDIDO AS purchase_order
            FROM SC1010 C1 WITH (NOLOCK)
            LEFT JOIN SA2010 SA2 WITH (NOLOCK)
                ON SA2.A2_COD = C1.C1_FORNECE
               AND SA2.A2_LOJA = C1.C1_LOJA
               AND SA2.D_E_L_E_T_ = ''
            WHERE C1.D_E_L_E_T_ = ''
              AND C1.C1_PRODUTO = ?
              AND C1.C1_EMISSAO >= ?
              AND C1.C1_EMISSAO < ?
              {branch_filter_sc}
        ),
        PEDIDOS AS (
            SELECT
                'SC7010' AS source,
                C7.C7_FILIAL AS branch,
                C7.C7_NUM AS document_number,
                C7.C7_ITEM AS item,
                C7.C7_EMISSAO AS issue_date,
                C7.C7_DATPRF AS required_date,
                C7.C7_FORNECE AS supplier_code,
                C7.C7_LOJA AS supplier_store,
                SA2.A2_NOME AS supplier_name,
                C7.C7_QUANT AS quantity,
                C7.C7_PRECO AS unit_price,
                C7.C7_TOTAL AS total_value,
                CAST(NULL AS VARCHAR(20)) AS purchase_order
            FROM SC7010 C7 WITH (NOLOCK)
            LEFT JOIN SA2010 SA2 WITH (NOLOCK)
                ON SA2.A2_COD = C7.C7_FORNECE
               AND SA2.A2_LOJA = C7.C7_LOJA
               AND SA2.D_E_L_E_T_ = ''
            WHERE C7.D_E_L_E_T_ = ''
              AND C7.C7_PRODUTO = ?
              AND C7.C7_EMISSAO >= ?
              AND C7.C7_EMISSAO < ?
              {branch_filter_pc}
        )
        SELECT *
        FROM (
            SELECT * FROM REQUISICOES
            UNION ALL
            SELECT * FROM PEDIDOS
        ) H
        ORDER BY issue_date DESC, source DESC, document_number DESC
        """
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))

# app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class FinancialRepository(BaseRepository, FinancialQueryRepositoryPort):

    def get_rol(self, request: GetRolRequest) -> dict:
        vendas_qb = QueryBuilder()
        vendas_qb.raw("D2.D_E_L_E_T_ = ''")
        if request.branch:
            vendas_qb.eq("D2.D2_FILIAL", request.branch)
        vendas_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        vendas_where, vendas_params = vendas_qb.build()

        exists_qb = QueryBuilder()
        exists_qb.date_range("D1X.D1_DTDIGIT", request.start_date, request.end_date)
        exists_where, exists_params = exists_qb.build()

        dev_qb = QueryBuilder()
        dev_qb.raw("D1.D_E_L_E_T_ = ''")
        if request.branch:
            dev_qb.eq("D1.D1_FILIAL", request.branch)
        dev_qb.date_range("D1.D1_DTDIGIT", request.start_date, request.end_date)
        dev_where, dev_params = dev_qb.build()

        sql = f"""
        WITH VENDAS AS (
            SELECT
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_TOTAL, 0))) AS VALOR_BRUTO_VENDA,

                SUM(CONVERT(FLOAT,
                    ISNULL(D2.D2_DESCON, 0)
                    + ISNULL(D2.D2_DESC, 0)
                )) AS VALOR_DESCONTOS,

                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALICM, 0)))  AS VALOR_ICMS,
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALIMP5, 0))) AS VALOR_PIS,
                SUM(CONVERT(FLOAT, ISNULL(D2.D2_VALIMP6, 0))) AS VALOR_COFINS,

                SUM(CONVERT(FLOAT,
                    ISNULL(D2.D2_TOTAL, 0)
                    - ISNULL(D2.D2_VALICM, 0)
                    - ISNULL(D2.D2_VALIMP5, 0)
                    - ISNULL(D2.D2_VALIMP6, 0)
                )) AS VLR_VENDA,

                MIN(D2.D2_EMISSAO) AS MIN_EMISSAO,
                MAX(D2.D2_EMISSAO) AS MAX_EMISSAO

            FROM SD2010 D2

            LEFT JOIN SA1010 A1
                ON  A1.D_E_L_E_T_ = ''
                AND A1.A1_COD  = D2.D2_CLIENTE
                AND A1.A1_LOJA = D2.D2_LOJA

            LEFT JOIN SF4010 F4
                ON  F4.D_E_L_E_T_ = ''
                AND F4.F4_CODIGO = D2.D2_TES
                AND (
                        F4.F4_FILIAL = D2.D2_FILIAL
                     OR F4.F4_FILIAL = ''
                     OR F4.F4_FILIAL IS NULL
                )

            WHERE {vendas_where}
                AND ISNULL(A1.A1_NOME, '') <> ''
                AND ISNULL(D2.D2_TIPO, '') <> 'D'

                AND (
                    D2.D2_CF NOT IN ('5911', '6151')
                    OR (
                        D2.D2_FILIAL = '01'
                        AND D2.D2_CF IN ('5911', '6911')
                        AND D2.D2_COD LIKE '90%'
                        AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND D2.D2_UM = 'MI'
                    )
                )

                AND (
                    ISNULL(F4.F4_DUPLIC, '') = 'S'

                    OR (
                        ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND ISNULL(F4.F4_FINALID, '') = 'BAIXA ESTOQUE'
                        AND D2.D2_CF  = '5927'
                        AND D2.D2_UM  = 'MI'
                        AND EXISTS (
                            SELECT 1
                            FROM SD1010 D1X
                            WHERE
                                D1X.D_E_L_E_T_ = ''
                                AND D1X.D1_FILIAL  = D2.D2_FILIAL
                                AND D1X.D1_FORNECE = D2.D2_CLIENTE
                                AND D1X.D1_LOJA    = D2.D2_LOJA
                                AND {exists_where}
                                AND (
                                    D1X.D1_CF IN ('1201', '2201')
                                    OR D1X.D1_TIPO = 'D'
                                )
                        )
                    )

                    OR (
                        D2.D2_FILIAL = '01'
                        AND D2.D2_CF IN ('5911', '6911')
                        AND D2.D2_COD LIKE '90%'
                        AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                        AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                        AND D2.D2_UM = 'MI'
                    )
                )
        ),

        DEVOLUCOES AS (
            SELECT
                SUM(CONVERT(FLOAT,
                    ISNULL(D1.D1_TOTAL, 0)
                    - ISNULL(D1.D1_VALICM, 0)
                    - ISNULL(D1.D1_VALIMP5, 0)
                    - ISNULL(D1.D1_VALIMP6, 0)
                )) AS VLR_DEVOLUCAO

            FROM SD1010 D1

            WHERE {dev_where}
                AND (
                    D1.D1_CF IN ('1201', '2201')
                    OR D1.D1_TIPO = 'D'
                )
        )

        SELECT
            ? AS branch,

            ISNULL(V.MIN_EMISSAO, '') AS start_date,
            ISNULL(V.MAX_EMISSAO, '') AS end_date,

            ISNULL(V.VALOR_BRUTO_VENDA, 0) AS gross_revenue,
            0 AS other_values,
            0 AS items_without_tes,
            ISNULL(D.VLR_DEVOLUCAO, 0) AS returns,
            ISNULL(V.VALOR_DESCONTOS, 0) AS discounts,

            ISNULL(V.VALOR_ICMS, 0)  AS icms,
            0 AS iss,
            ISNULL(V.VALOR_PIS, 0)   AS pis,
            ISNULL(V.VALOR_COFINS, 0) AS cofins,
            0 AS ipi_separated,

            ISNULL(V.VALOR_ICMS, 0)
            + ISNULL(V.VALOR_PIS, 0)
            + ISNULL(V.VALOR_COFINS, 0) AS rol_taxes,

            ISNULL(V.VLR_VENDA, 0)
            - ISNULL(D.VLR_DEVOLUCAO, 0) AS rol,

            ISNULL(V.VLR_VENDA, 0)
            - ISNULL(D.VLR_DEVOLUCAO, 0) AS rol_with_ipi,

            0 AS financial_titles,
            0 AS financial_balance

        FROM (SELECT 1 AS _) AS _pivot
        LEFT JOIN VENDAS V ON 1=1
        LEFT JOIN DEVOLUCOES D ON 1=1
        """

        branch_label = request.branch or "consolidated"
        params = vendas_params + exists_params + dev_params + (branch_label,)

        with self as repo:
            result = repo.execute_one(sql, params)

        return result or {
            "branch": branch_label,
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "gross_revenue": 0,
            "other_values": 0,
            "items_without_tes": 0,
            "returns": 0,
            "discounts": 0,
            "icms": 0,
            "iss": 0,
            "pis": 0,
            "cofins": 0,
            "ipi_separated": 0,
            "rol_taxes": 0,
            "rol": 0,
            "rol_with_ipi": 0,
            "financial_titles": 0,
            "financial_balance": 0,
        }

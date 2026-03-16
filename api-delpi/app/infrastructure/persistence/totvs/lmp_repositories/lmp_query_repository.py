# app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_repository.py
from typing import List
from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_product import LMPProduct
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.infrastructure.persistence.query_builder import QueryBuilder


class LMPQueryRepository(BaseRepository, LMPQueryRepositoryPort):

    # =========================
    # SQL BLOCKS
    # =========================

    def _sql_historico_ov_cte(self) -> str:
        return """
            HistoricoOV AS (
                SELECT
                    A.AIJ_NROPOR,
                    MAX(A.AIJ_DTINIC) AS AIJ_DTINIC,
                    MAX(A.AIJ_DTENCE) AS AIJ_DTENCE
                FROM AIJ010 A
                WHERE A.D_E_L_E_T_ = ''
                  AND A.AIJ_STAGE = '000012'
                  AND A.AIJ_FILIAL = '01'
                GROUP BY A.AIJ_NROPOR
            )
        """

    def _sql_produtos_lmp_cte(self) -> str:
        return """
            ProdutosLMP AS (
                SELECT DISTINCT
                    ADJ.ADJ_NROPOR,
                    ADJ.ADJ_REVISA,
                    ADJ.ADJ_PROD
                FROM ADJ010 ADJ
                INNER JOIN AD1010 AD1
                    ON AD1.AD1_NROPOR = ADJ.ADJ_NROPOR
                AND AD1.AD1_REVISA = ADJ.ADJ_REVISA
                AND AD1.D_E_L_E_T_ = ''
                AND AD1.AD1_FILIAL = '01'
                WHERE ADJ.D_E_L_E_T_ = ''
                AND ADJ.ADJ_FILIAL = '01'
            )
        """

    def _sql_pi_por_referencia_ctes_from_produtos_lmp(self) -> str:
        return """
            ProdutosLMPRef AS (
                SELECT
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    P.ADJ_PROD,
                    SB1.B1_REFEREN
                FROM ProdutosLMP P
                INNER JOIN SB1010 SB1
                    ON SB1.B1_COD = P.ADJ_PROD
                   AND SB1.D_E_L_E_T_ = ''
                WHERE SB1.B1_REFEREN <> ''
            ),

            ProdutosBase AS (
                SELECT DISTINCT
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    SB.B1_COD AS ROOT_PRODUCT,
                    SB.B1_REFEREN
                FROM ProdutosLMPRef R
                INNER JOIN SB1010 SB
                    ON SB.B1_REFEREN = R.B1_REFEREN
                   AND SB.D_E_L_E_T_ = ''
                   AND SB.B1_TIPO = 'PA'
            ),

            Recursive_BOM AS (
                SELECT
                    B.ADJ_NROPOR,
                    B.ADJ_REVISA,
                    B.ADJ_PROD,
                    B.ROOT_PRODUCT,
                    G.G1_COMP AS COMPONENT,
                    1 AS LEVEL
                FROM ProdutosBase B
                INNER JOIN SG1010 G
                    ON G.G1_COD = B.ROOT_PRODUCT
                WHERE G.D_E_L_E_T_ = ''
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    R.ROOT_PRODUCT,
                    G.G1_COMP,
                    R.LEVEL + 1
                FROM SG1010 G
                INNER JOIN Recursive_BOM R
                    ON R.COMPONENT = G.G1_COD
                WHERE G.D_E_L_E_T_ = ''
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
                  AND R.LEVEL < 999
            ),

            PI_COUNT_BY_PRODUCT AS (
                SELECT
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    COUNT(DISTINCT SB.B1_COD) AS QTD_PI
                FROM Recursive_BOM R
                INNER JOIN SB1010 SB
                    ON SB.B1_COD = R.COMPONENT
                   AND SB.B1_TIPO = 'PI'
                   AND SB.D_E_L_E_T_ = ''
                GROUP BY
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD
            ),

            PI_COUNT_BY_OV AS (
                SELECT
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    SUM(P.QTD_PI) AS QTD_PI
                FROM PI_COUNT_BY_PRODUCT P
                GROUP BY
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA
            )
        """

    def _sql_header_lmp(self) -> str:
        return f"""
            WITH
            {self._sql_historico_ov_cte()}
            SELECT TOP 1
                AD1.AD1_NROPOR AS sale_number,
                AD1.AD1_DESCRI AS sale_description,
                H.AIJ_DTINIC AS start_date,
                H.AIJ_DTENCE AS end_date,
                AD1.AD1_CODCLI AS costumer_code,
                AD1.AD1_LOJCLI AS costumer_store,
                SA1.A1_NOME AS costumer_name,
                AD1.AD1_VEND AS seller_code,
                SA3.A3_NOME AS seller_name
            FROM AD1010 AD1
            LEFT JOIN HistoricoOV H
                ON H.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN SA1010 SA1
                ON SA1.A1_COD = AD1.AD1_CODCLI
               AND SA1.A1_LOJA = AD1.AD1_LOJCLI
               AND SA1.D_E_L_E_T_ = ''
            LEFT JOIN SA3010 SA3
                ON SA3.A3_COD = AD1.AD1_VEND
               AND SA3.D_E_L_E_T_ = ''
            WHERE AD1.D_E_L_E_T_ = ''
              AND AD1.AD1_FILIAL = '01'
              AND AD1.AD1_NROPOR = ?
        """

    def _sql_products_lmp(self) -> str:
        return f"""
            WITH
            {self._sql_produtos_lmp_cte()},
            {self._sql_pi_por_referencia_ctes_from_produtos_lmp()}
            SELECT
                SB1.B1_GRUPO    AS group_code,
                SB1.B1_COD      AS code,
                SB1.B1_DESC     AS description,
                SB1.B1_TIPO     AS type,
                ISNULL(PI.QTD_PI, 0) AS qtd_pi
            FROM ProdutosLMP P
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = P.ADJ_PROD
               AND SB1.D_E_L_E_T_ = ''
            LEFT JOIN PI_COUNT_BY_PRODUCT PI
                ON PI.ADJ_NROPOR = P.ADJ_NROPOR
               AND PI.ADJ_REVISA = P.ADJ_REVISA
               AND PI.ADJ_PROD = P.ADJ_PROD
            WHERE P.ADJ_NROPOR = ?
            ORDER BY SB1.B1_COD
        """

    def _sql_qtd_pi_lmp_total(self) -> str:
        return f"""
            WITH
            {self._sql_produtos_lmp_cte()},
            {self._sql_pi_por_referencia_ctes_from_produtos_lmp()}
            SELECT ISNULL(SUM(PI.QTD_PI), 0) AS qtd_pi
            FROM (
                SELECT DISTINCT
                    ADJ_NROPOR,
                    ADJ_REVISA,
                    QTD_PI
                FROM PI_COUNT_BY_OV
            ) PI
            WHERE PI.ADJ_NROPOR = ?
        """

    # =========================
    # PUBLIC METHODS
    # =========================

    def list_lmps(
        self,
        request: ListLMPRequest
    ) -> List[LMP]:

        qb = QueryBuilder()
        qb.date_range(
            field="H.AIJ_DTINIC",
            start=request.date_start,
            end=request.date_end
        )

        where_clause, params = qb.build()

        sql = f"""
            WITH
            CabecalhoOV AS (
                SELECT
                    AD1_FILIAL,
                    AD1_NROPOR,
                    AD1_REVISA,
                    AD1_DESCRI
                FROM AD1010
                WHERE D_E_L_E_T_ = ''
                  AND AD1_FILIAL = '01'
            ),
            {self._sql_historico_ov_cte()},
            {self._sql_produtos_lmp_cte()},
            {self._sql_pi_por_referencia_ctes_from_produtos_lmp()}
            SELECT
                C.AD1_NROPOR AS sale_number,
                C.AD1_DESCRI AS sale_description,
                H.AIJ_DTINIC AS start_date,
                H.AIJ_DTENCE AS end_date,
                ISNULL(PI.QTD_PI, 0) AS qtd_pi
            FROM CabecalhoOV C
            INNER JOIN HistoricoOV H
                ON H.AIJ_NROPOR = C.AD1_NROPOR
            LEFT JOIN PI_COUNT_BY_OV PI
                ON PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
            WHERE {where_clause}
            GROUP BY
                C.AD1_NROPOR,
                C.AD1_DESCRI,
                H.AIJ_DTINIC,
                H.AIJ_DTENCE,
                PI.QTD_PI
        """

        with self as repo:
            rows = repo.execute_query(sql, params)
            return [LMP(**row) for row in rows]

    def get_lmp(
        self,
        request: GetLMPRequest
    ) -> LMP:

        with self as repo:
            header_row = repo.execute_one(self._sql_header_lmp(), (request.sale_number,))

            if not header_row:
                raise ValueError(f"LMP não encontrada: {request.sale_number}")

            product_rows = repo.execute_query(self._sql_products_lmp(), (request.sale_number,))
            qtd_pi = repo.execute_scalar(self._sql_qtd_pi_lmp_total(), (request.sale_number,))

        products = [LMPProduct(**row) for row in product_rows]

        return LMP(
            sale_number=header_row["sale_number"],
            sale_description=header_row["sale_description"],
            start_date=header_row.get("start_date"),
            end_date=header_row.get("end_date"),
            qtd_pi=int(qtd_pi or 0),
            costumer_code=header_row.get("costumer_code"),
            costumer_store=header_row.get("costumer_store"),
            costumer_name=header_row.get("costumer_name"),
            seller_code=header_row.get("seller_code"),
            seller_name=header_row.get("seller_name"),
            inclusion_user=header_row.get("inclusion_user"),
            list_products=products
        )
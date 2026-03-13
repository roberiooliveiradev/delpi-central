# app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_repository.py
from typing import List
from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.entities.lmp.lmp import LMP
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.infrastructure.persistence.query_builder import QueryBuilder
from app.application.models.page import Page


class LMPQueryRepository(BaseRepository, LMPQueryRepositoryPort):

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

        sql=f"""
            WITH CabecalhoOV AS (
                SELECT 
                    AD1_FILIAL,
                    AD1_NROPOR,
                    AD1_REVISA,
                    AD1_DESCRI
                FROM AD1010
                WHERE D_E_L_E_T_ = ''
                AND AD1_FILIAL = '01'
            ),

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
            ),

            Prod_Cat_OV AS (
                SELECT
                    ADJ.ADJ_NROPOR,
                    ADJ.ADJ_REVISA,
                    SB1.B1_REFEREN
                FROM ADJ010 ADJ
                INNER JOIN SB1010 SB1
                    ON SB1.B1_COD = ADJ.ADJ_PROD
                AND SB1.D_E_L_E_T_ = ''
                WHERE ADJ.D_E_L_E_T_ = ''
                AND ADJ.ADJ_FILIAL = '01'
                AND SB1.B1_REFEREN <> ''
            ),

            -- PRODUTOS NECESSÁRIOS
            ProdutosBase AS (
                SELECT DISTINCT
                    SB.B1_COD,
                    SB.B1_REFEREN
                FROM SB1010 SB
                INNER JOIN Prod_Cat_OV P
                    ON P.B1_REFEREN = SB.B1_REFEREN
                WHERE SB.D_E_L_E_T_ = ''
                AND SB.B1_TIPO = 'PA'
            ),

            -- RECURSÃO APENAS NOS PRODUTOS NECESSÁRIOS
            Recursive_BOM AS (

                SELECT
                    B.B1_COD AS ROOT_PRODUCT,
                    G.G1_COMP AS COMPONENT,
                    1 AS LEVEL
                FROM ProdutosBase B
                INNER JOIN SG1010 G
                    ON G.G1_COD = B.B1_COD
                WHERE G.D_E_L_E_T_ = ''
                AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT
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

            PI_COUNT AS (
                SELECT
                    R.ROOT_PRODUCT,
                    COUNT(DISTINCT SB.B1_COD) AS QTD_PI
                FROM Recursive_BOM R
                INNER JOIN SB1010 SB
                    ON SB.B1_COD = R.COMPONENT
                AND SB.B1_TIPO = 'PI'
                AND SB.D_E_L_E_T_ = ''
                GROUP BY R.ROOT_PRODUCT
            ),

            Produto AS (
                SELECT
                    B.B1_REFEREN,
                    SUM(ISNULL(P.QTD_PI,0)) AS QTD_PI
                FROM ProdutosBase B
                LEFT JOIN PI_COUNT P
                    ON P.ROOT_PRODUCT = B.B1_COD
                GROUP BY B.B1_REFEREN
            )

            SELECT
                C.AD1_NROPOR AS sale_number,
                C.AD1_DESCRI AS sale_description,
                H.AIJ_DTINIC AS start_date,
                H.AIJ_DTENCE AS end_date,
                SUM(P.QTD_PI) AS qtd_pi
            FROM CabecalhoOV C
            INNER JOIN Prod_Cat_OV PC
                ON PC.ADJ_NROPOR = C.AD1_NROPOR
            AND PC.ADJ_REVISA = C.AD1_REVISA
            INNER JOIN HistoricoOV H
                ON H.AIJ_NROPOR = PC.ADJ_NROPOR
            INNER JOIN Produto P
                ON P.B1_REFEREN = PC.B1_REFEREN
            WHERE
                {where_clause}
            GROUP BY
                C.AD1_NROPOR,
                C.AD1_DESCRI,
                H.AIJ_DTINIC,
                H.AIJ_DTENCE;
        """
        with self as repo:

            rows = repo.execute_query(sql, params)

            items = [
                LMP(**row)
                for row in rows
            ]

            return items
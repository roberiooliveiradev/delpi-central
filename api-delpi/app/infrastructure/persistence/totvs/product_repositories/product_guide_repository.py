# app/infrastructure/persistence/totvs/product_repositories/product_guide_repository.py

from typing import Optional

from app.infrastructure.persistence.base_repository import BaseRepository
from app.infrastructure.persistence.query_builder import QueryBuilder

from app.domain.entities.guide_operation import GuideOperation
from app.domain.ports.product_guide_repository_port import ProductGuideRepositoryPort


class ProductGuideRepository(BaseRepository, ProductGuideRepositoryPort):

    def fetch_guide_rows(
        self,
        code: str,
        branch: Optional[str],
        max_depth: int
    ):

        qb = QueryBuilder()

        qb.raw("SG2.D_E_L_E_T_ = ''")
        qb.eq("SG2.G2_FILIAL", branch)

        where_clause, params = qb.build()

        sql = f"""  
        WITH RECURSIVE_BOM AS (
            SELECT
                G1_COD  AS parent_code,
                G1_COMP AS product_code,
                1       AS bom_level
            FROM SG1010
            WHERE D_E_L_E_T_ = ''
            AND G1_COD = ?

            UNION ALL

            SELECT
                C.G1_COD,
                C.G1_COMP,
                B.bom_level + 1
            FROM SG1010 C
            INNER JOIN RECURSIVE_BOM B
                ON B.product_code = C.G1_COD
            WHERE C.D_E_L_E_T_ = ''
            AND B.bom_level < ?
        ),
        CODES AS (
            SELECT ? AS product_code, 0 AS bom_level
            UNION ALL
            SELECT DISTINCT product_code, bom_level FROM RECURSIVE_BOM
        )
        SELECT
            SG2.G2_FILIAL  AS branch,
            SG2.G2_CODIGO  AS route_code,
            SG2.G2_PRODUTO AS product_code,
            SG2.G2_OPERAC  AS operation_code,
            SG2.G2_DESCRI  AS operation_description,

            SG2.G2_RECURSO AS resource_code,
            SG2.G2_CTRAB   AS work_center,

            SG2.G2_SETUP                    AS setup_hours, 
            SG2.G2_TEMPAD                   AS standard_time_hour_mil, 
            SG2.G2_TEMPAD / 1000.0          AS standard_time_hours_piece, 
            (SG2.G2_TEMPAD / 1000.0) * 60   AS standard_time_minutes_piece, 

            SG2.G2_TPOPER  AS operation_type,
            SG2.G2_OPE_OBR AS mandatory_operation,
            SG2.G2_SEQ_OBR AS mandatory_sequence,
            SG2.G2_LAU_OBR AS mandatory_report,

            SGF.GF_COMP    AS component_code,
            SB1.B1_DESC    AS component_description,
            SGF.GF_TRT     AS component_sequence,

            CODES.bom_level AS bom_level

        FROM SG2010 SG2
        INNER JOIN CODES
            ON CODES.product_code = SG2.G2_PRODUTO

        LEFT JOIN SGF010 SGF
            ON SGF.GF_FILIAL  = SG2.G2_FILIAL
        AND SGF.GF_PRODUTO = SG2.G2_PRODUTO
        AND SGF.GF_ROTEIRO = SG2.G2_CODIGO
        AND SGF.GF_OPERAC  = SG2.G2_OPERAC
        AND SGF.D_E_L_E_T_ = ''

        LEFT JOIN SB1010 SB1
            ON SB1.B1_COD = SGF.GF_COMP
        AND SB1.D_E_L_E_T_ = ''

        WHERE {where_clause}

        ORDER BY
            CODES.bom_level,
            SG2.G2_PRODUTO,
            SG2.G2_OPERAC,
            SGF.GF_TRT
        """

        base_params = (code, max_depth, code)

        with self as repo:

            rows = repo.execute_query(
                sql,
                base_params + params
            )

        return [
            GuideOperation(
                branch=r["branch"],
                route_code=r["route_code"],
                product_code=r["product_code"],
                operation_code=r["operation_code"],
                operation_description=r["operation_description"],
                resource_code=r["resource_code"],
                work_center=r["work_center"],
                setup_hours=r["setup_hours"],
                standard_time_hour_mil=r["standard_time_hour_mil"],
                standard_time_hours_piece=r["standard_time_hours_piece"],
                standard_time_minutes_piece=r["standard_time_minutes_piece"],
                operation_type=r["operation_type"],
                mandatory_operation=r["mandatory_operation"],
                mandatory_sequence=r["mandatory_sequence"],
                mandatory_report=r["mandatory_report"],
                component_code=r["component_code"],
                component_description=r["component_description"],
                component_sequence=r["component_sequence"],
                bom_level=r["bom_level"],
            )
            for r in rows
        ]
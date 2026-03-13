# app/infrastructure/persistence/totvs/product_repositories/product_inspection_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.ports.product.product_inspection_repository_port import ProductInspectionRepositoryPort
from app.domain.entities.product.inspection import Inspection


class ProductInspectionRepository(BaseRepository, ProductInspectionRepositoryPort):

    def fetch_inspection_rows(self, code: str, max_depth: int):

        sql = """   
        DECLARE
            @product_code NVARCHAR(20) = ?,
            @max_depth INT = ?;

        -- ============================================================
        -- Product structure (SG1010)
        -- ============================================================
        WITH bom_recursive AS (
            SELECT
                G1.G1_COD  AS root_code,
                G1.G1_COMP AS product_code,
                1          AS bom_level
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
            AND G1.G1_COD = @product_code

            UNION ALL

            SELECT
                B.root_code,
                G1.G1_COMP,
                B.bom_level + 1
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN bom_recursive B
                ON B.product_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
            AND B.bom_level < @max_depth
        ),

        product_scope AS (
            SELECT @product_code AS product_code, 0 AS bom_level
            UNION
            SELECT product_code, bom_level FROM bom_recursive
        ),

        -- ============================================================
        -- Active revision per product (QP6)
        -- ============================================================
        active_qp6 AS (
            SELECT
                QP6_PRODUT AS product_code,
                MAX(QP6_REVI) AS revision
            FROM QP6010
            WHERE D_E_L_E_T_ = ''
            GROUP BY QP6_PRODUT
        ),

        -- ============================================================
        -- Products with valid inspection definition
        -- ============================================================
        inspection_scope AS (
            SELECT
                P.product_code AS product_code,
                P.bom_level    AS bom_level,
                R.revision     AS revision
            FROM product_scope P
            INNER JOIN active_qp6 R
                ON R.product_code = P.product_code
        )

        -- ============================================================
        -- Final JSON
        -- ============================================================
        SELECT
        (
            SELECT
                COUNT(*) AS total,
                (
                    SELECT
                        I.product_code,
                        I.bom_level,

                        CASE
                            WHEN EXISTS (
                                SELECT 1
                                FROM QP7010
                                WHERE D_E_L_E_T_ = ''
                                AND QP7_PRODUT = I.product_code
                                AND QP7_REVI = I.revision
                            )
                            OR EXISTS (
                                SELECT 1
                                FROM QP8010
                                WHERE D_E_L_E_T_ = ''
                                AND QP8_PRODUT = I.product_code
                                AND QP8_REVI = I.revision
                            )
                            THEN CAST(1 AS BIT)
                            ELSE CAST(0 AS BIT)
                        END AS has_inspection,

                        -- =========================
                        -- QP6 — Inspection header
                        -- =========================
                        (
                            SELECT
                                QP6.QP6_PRODUT  AS product_code,
                                QP6.QP6_REVI    AS revision,
                                QP6.QP6_REVINV  AS review_invalid,
                                QP6.QP6_DESCPO  AS description,
                                QP6.QP6_DTCAD   AS created_at,
                                QP6.QP6_DTINI   AS start_date,
                                QP6.QP6_CADR    AS created_by,
                                QP6.QP6_PTOLER  AS tolerance_percent,
                                QP6.QP6_TIPO    AS inspection_type,
                                QP6.QP6_DOCOBR  AS requires_document,
                                QP6.QP6_SITPRD  AS product_status,
                                QP6.QP6_DESSTP  AS status_description,
                                QP6.QP6_UNMED1  AS unit
                            FROM QP6010 QP6 WITH (NOLOCK)
                            WHERE QP6.D_E_L_E_T_ = ''
                            AND QP6.QP6_PRODUT = I.product_code
                            AND QP6.QP6_REVI = I.revision
                            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                        ) AS header,

                        -- =========================
                        -- QP7 — Measurable tests
                        -- =========================
                        (
                            SELECT
                                QP7.QP7_PRODUT  AS product_code,
                                QP7.QP7_REVI    AS revision,
                                QP7.QP7_ENSAIO  AS test_code,
                                QP7.QP7_LABOR   AS labor,
                                QP7.QP7_SEQLAB  AS sequence,
                                QP7.QP7_UNIMED  AS unit,
                                QP7.QP7_MINMAX  AS min_max_type,
                                QP7.QP7_NOMINA  AS nominal_value,
                                QP7.QP7_LIE     AS lower_spec_limit,
                                QP7.QP7_LSE     AS upper_spec_limit,
                                QP7.QP7_LIC     AS lower_control_limit,
                                QP7.QP7_LSC     AS upper_control_limit,
                                QP7.QP7_CODREC  AS reaction_code,
                                QP7.QP7_OPERAC  AS operation,
                                QP7.QP7_ENSOBR  AS mandatory,
                                QP7.QP7_CERTIF  AS certification
                            FROM QP7010 QP7 WITH (NOLOCK)
                            WHERE QP7.D_E_L_E_T_ = ''
                            AND QP7.QP7_PRODUT = I.product_code
                            AND QP7.QP7_REVI = I.revision
                            FOR JSON PATH
                        ) AS measurable_tests,

                        -- =========================
                        -- QP8 — Textual tests
                        -- =========================
                        (
                            SELECT
                                QP8.QP8_PRODUT  AS product_code,
                                QP8.QP8_REVI    AS revision,
                                QP8.QP8_ENSAIO  AS test_code,
                                QP8.QP8_LABOR   AS labor,
                                QP8.QP8_SEQLAB  AS sequence,
                                QP8.QP8_TEXTO   AS text,
                                QP8.QP8_CODREC  AS reaction_code,
                                QP8.QP8_OPERAC  AS operation,
                                QP8.QP8_ENSOBR  AS mandatory,
                                QP8.QP8_CERTIF  AS certification
                            FROM QP8010 QP8 WITH (NOLOCK)
                            WHERE QP8.D_E_L_E_T_ = ''
                            AND QP8.QP8_PRODUT = I.product_code
                            AND QP8.QP8_REVI = I.revision
                            FOR JSON PATH
                        ) AS textual_tests

                    FROM inspection_scope I
                    ORDER BY I.bom_level, I.product_code
                    FOR JSON PATH
                ) AS data
            FROM inspection_scope
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        ) AS data;
        """

        with self as repo:
            result = repo.execute_json(sql, (code, max_depth))

        inspections = []

        for r in result.get("data", []):
            inspections.append(
                Inspection(
                    product_code=r.get("product_code"),
                    bom_level=r.get("bom_level"),
                    has_inspection=r.get("has_inspection"),
                    header=r.get("header"),
                    measurable_tests=r.get("measurable_tests") or [],
                    textual_tests=r.get("textual_tests") or [],
                )
            )

        return inspections
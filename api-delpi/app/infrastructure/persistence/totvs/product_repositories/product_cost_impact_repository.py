from app.domain.ports.product.product_cost_impact_repository_port import (
    ProductCostImpactRepositoryPort,
)
from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_BOM_VALIDITY = ProductBomValidityFilterService.validity_filter_sql_for_today(alias="G1")


class ProductCostImpactRepository(BaseRepository, ProductCostImpactRepositoryPort):

    def fetch_product_cost_header(self, code: str) -> dict | None:
        sql = """
        SELECT TOP 1
            B1_COD  AS product_code,
            B1_DESC AS description,
            B1_TIPO AS product_type,
            B1_UM   AS unit,
            B1_GRUPO AS group_code,
            B1_CUSTD AS standard_cost,
            B1_UCALSTD AS standard_cost_date,
            B1_UPRC AS last_purchase_price,
            B1_UCOM AS last_purchase_date
        FROM SB1010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND B1_COD = ?
        """
        with self as repo:
            return repo.execute_one(sql, (code,))

    def fetch_raw_material_cost_items(self, code: str, max_depth: int) -> list[dict]:
        sql = f"""
        DECLARE @PRODUTO VARCHAR(30) = ?;
        DECLARE @MAX_DEPTH INT = ?;

        WITH ESTRUTURA AS (
            SELECT
                G1.G1_COD AS parent_code,
                G1.G1_COMP AS component_code,
                CAST(G1.G1_QUANT AS FLOAT) AS quantity_per,
                CAST(G1.G1_QUANT AS FLOAT) AS accumulated_quantity,
                1 AS level,
                CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS path
            FROM SG1010 G1 WITH (NOLOCK)
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_COD = @PRODUTO
              {_BOM_VALIDITY}

            UNION ALL

            SELECT
                G1.G1_COD,
                G1.G1_COMP,
                CAST(G1.G1_QUANT AS FLOAT),
                CAST(E.accumulated_quantity * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT),
                E.level + 1,
                CAST(E.path + ' > ' + G1.G1_COMP AS VARCHAR(MAX))
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN ESTRUTURA E
                ON E.component_code = G1.G1_COD
            WHERE G1.D_E_L_E_T_ = ''
              AND E.level < @MAX_DEPTH
              {_BOM_VALIDITY}
        ),

        RAW_MATERIALS AS (
            SELECT
                E.component_code AS raw_material_code,
                SUM(E.accumulated_quantity) AS quantity_per_pa,
                MIN(E.path) AS sample_path
            FROM ESTRUTURA E
            INNER JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = E.component_code
               AND SB1.D_E_L_E_T_ = ''
               AND SB1.B1_TIPO = 'MP'
            GROUP BY E.component_code
        )

        SELECT
            RM.raw_material_code,
            SB1.B1_DESC AS raw_material_description,
            SB1.B1_UM AS unit,
            SB1.B1_GRUPO AS group_code,
            CAST(RM.quantity_per_pa AS VARCHAR(50)) AS quantity_per_pa,
            CAST(SB1.B1_CUSTD AS VARCHAR(50)) AS standard_cost,
            CAST(SB1.B1_UPRC AS VARCHAR(50)) AS last_purchase_price,
            RM.sample_path AS path
        FROM RAW_MATERIALS RM
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = RM.raw_material_code
           AND SB1.D_E_L_E_T_ = ''
        ORDER BY RM.raw_material_code
        OPTION (MAXRECURSION 0);
        """
        with self as repo:
            return repo.execute_batch_query(sql, (code, max_depth))

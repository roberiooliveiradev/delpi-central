# app/infrastructure/persistence/totvs/product_repositories/product_structure_repository.py

from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.ports.product.product_structure_repository_port import ProductStructureRepositoryPort

_BOM_VALIDITY = ProductBomValidityFilterService.validity_filter_sql_for_today()
_BOM_VALIDITY_RECURSIVE = ProductBomValidityFilterService.validity_filter_sql_for_today(alias="c")


class ProductStructureRepository(BaseRepository, ProductStructureRepositoryPort):

    def fetch_structure_rows(self, code: str, max_depth: int):

        sql = f"""
        WITH recursive_bom AS (
            SELECT 
                G1_COD   AS parent_code,
                G1_COMP  AS component_code,
                G1_QUANT AS quantity,
                1        AS bom_level
            FROM SG1010
            WHERE D_E_L_E_T_ = ''
            AND G1_COD = ?
            {_BOM_VALIDITY}

            UNION ALL

            SELECT 
                c.G1_COD,
                c.G1_COMP,
                c.G1_QUANT,
                p.bom_level + 1
            FROM SG1010 c
            INNER JOIN recursive_bom p
                ON p.component_code = c.G1_COD
            WHERE c.D_E_L_E_T_ = ''
            AND p.bom_level < ?
            {_BOM_VALIDITY_RECURSIVE}
        )
        SELECT 
            rb.parent_code,
            parent.B1_DESC AS parent_description,
            parent.B1_TIPO AS parent_type,
            parent.B1_UM   AS parent_unit,

            rb.component_code,
            comp.B1_DESC   AS component_description,
            comp.B1_TIPO   AS component_type,
            comp.B1_UM     AS component_unit,
            comp.B1_SEGUM  AS component_secondary_unit,
            comp.B1_CONV   AS component_conversion_factor,
            comp.B1_TIPCONV AS component_conversion_type,

            rb.quantity,
            rb.bom_level
        FROM recursive_bom rb
        LEFT JOIN SB1010 parent
            ON parent.B1_COD = rb.parent_code
        LEFT JOIN SB1010 comp
            ON comp.B1_COD = rb.component_code
        ORDER BY
            rb.bom_level,
            rb.parent_code,
            rb.component_code
        """

        with self as repo:
            return repo.execute_query(sql, (code, max_depth))

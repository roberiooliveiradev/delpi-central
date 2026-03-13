# app/infrastructure/persistence/totvs/product_repositories/product_parents_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.ports.product.product_parents_repository_port import ProductParentsRepositoryPort


class ProductParentsRepository(BaseRepository, ProductParentsRepositoryPort):

    def fetch_parents_rows(self, code: str, max_depth: int):

        sql = """
        WITH recursive_parents AS (
            SELECT 
                G1_COD   AS parent_code,
                G1_COMP  AS child_code,
                G1_QUANT AS quantity,
                1        AS level
            FROM SG1010
            WHERE D_E_L_E_T_ = ''
            AND G1_COMP = ?

            UNION ALL

            SELECT 
                c.G1_COD,
                c.G1_COMP,
                c.G1_QUANT,
                p.level + 1
            FROM SG1010 c
            INNER JOIN recursive_parents p
                ON p.parent_code = c.G1_COMP
            WHERE c.D_E_L_E_T_ = ''
            AND p.level < ?
        )
        SELECT 
            rp.parent_code,
            parent.B1_DESC AS parent_description,
            parent.B1_TIPO AS parent_type,
            parent.B1_UM   AS parent_unit,

            rp.child_code,
            child.B1_DESC  AS child_description,
            child.B1_TIPO  AS child_type,
            child.B1_UM    AS child_unit,

            rp.quantity,
            rp.level
        FROM recursive_parents rp
        LEFT JOIN SB1010 parent
            ON parent.B1_COD = rp.parent_code
        LEFT JOIN SB1010 child
            ON child.B1_COD = rp.child_code
        ORDER BY
            rp.level,
            rp.parent_code,
            rp.child_code
        """

        with self as repo:
            return repo.execute_query(sql, (code, max_depth))
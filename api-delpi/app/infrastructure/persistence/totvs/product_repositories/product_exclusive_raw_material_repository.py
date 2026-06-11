# app/infrastructure/persistence/totvs/product_repositories/product_exclusive_raw_material_repository.py

from app.domain.constants.product_exclusivity import TEST_FINISHED_PRODUCT_PREFIXES
from app.domain.ports.product.product_exclusive_raw_material_repository_port import (
    ProductExclusiveRawMaterialRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class ProductExclusiveRawMaterialRepository(
    BaseRepository,
    ProductExclusiveRawMaterialRepositoryPort,
):

    def _test_product_filter(self, include_test_products: bool) -> str:
        if include_test_products:
            return ""
        return """
              AND PA.B1_COD NOT LIKE '8000%'
              AND PA.B1_COD NOT LIKE '8001%'
        """

    def _optional_filters(
        self,
        *,
        finished_product_code: str | None,
        raw_material_code: str | None,
        group_code: str | None,
    ) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []

        if finished_product_code:
            clauses.append("AND M.PA_RAIZ = ?")
            params.append(finished_product_code)

        if raw_material_code:
            clauses.append("AND M.COD_MP = ?")
            params.append(raw_material_code)

        if group_code:
            clauses.append("AND (M.GRUPO_MP = ? OR M.PA_GRUPO = ?)")
            params.extend([group_code, group_code])

        return "\n".join(clauses), params

    def _base_ctes(self, *, max_depth: int, include_test_products: bool) -> str:
        test_filter = self._test_product_filter(include_test_products)
        return f"""
        WITH ESTRUTURA_PA AS (
            SELECT
                PA.B1_COD  AS PA_RAIZ,
                PA.B1_DESC AS DESC_PA_RAIZ,
                PA.B1_UM   AS UNIDADE_PA,
                PA.B1_GRUPO AS PA_GRUPO,
                G1.G1_COD  AS PRODUTO_PAI,
                G1.G1_COMP AS COMPONENTE,
                1          AS NIVEL
            FROM SG1010 G1 WITH (NOLOCK)
            INNER JOIN SB1010 PA WITH (NOLOCK)
                ON PA.B1_COD = G1.G1_COD
               AND PA.D_E_L_E_T_ = ''
               AND PA.B1_TIPO = 'PA'
               {test_filter}
            WHERE G1.D_E_L_E_T_ = ''
              AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

            UNION ALL

            SELECT
                EP.PA_RAIZ,
                EP.DESC_PA_RAIZ,
                EP.UNIDADE_PA,
                EP.PA_GRUPO,
                G1.G1_COD,
                G1.G1_COMP,
                EP.NIVEL + 1
            FROM ESTRUTURA_PA EP
            INNER JOIN SG1010 G1 WITH (NOLOCK)
                ON G1.G1_COD = EP.COMPONENTE
               AND G1.D_E_L_E_T_ = ''
               AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
            WHERE EP.NIVEL < ?
        ),

        MP_POR_PA AS (
            SELECT DISTINCT
                EP.COMPONENTE AS COD_MP,
                MP.B1_DESC    AS DESC_MP,
                MP.B1_UM      AS UNIDADE_MP,
                MP.B1_GRUPO   AS GRUPO_MP,
                EP.PA_RAIZ,
                EP.DESC_PA_RAIZ,
                EP.UNIDADE_PA,
                EP.PA_GRUPO
            FROM ESTRUTURA_PA EP
            INNER JOIN SB1010 MP WITH (NOLOCK)
                ON MP.B1_COD = EP.COMPONENTE
               AND MP.D_E_L_E_T_ = ''
               AND MP.B1_TIPO = 'MP'
        ),

        MP_EXCLUSIVA AS (
            SELECT COD_MP
            FROM MP_POR_PA
            GROUP BY COD_MP
            HAVING COUNT(DISTINCT PA_RAIZ) = 1
        ),

        CATALOG AS (
            SELECT
                M.COD_MP AS raw_material_code,
                M.DESC_MP AS raw_material_description,
                M.UNIDADE_MP AS raw_material_unit,
                M.GRUPO_MP AS raw_material_group,
                M.PA_RAIZ AS finished_product_code,
                M.DESC_PA_RAIZ AS finished_product_description,
                M.UNIDADE_PA AS finished_product_unit
            FROM MP_POR_PA M
            INNER JOIN MP_EXCLUSIVA E
                ON E.COD_MP = M.COD_MP
            WHERE 1 = 1
        """

    def fetch_exclusive_catalog_totals(
        self,
        *,
        max_depth: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> dict:
        filter_sql, filter_params = self._optional_filters(
            finished_product_code=finished_product_code,
            raw_material_code=raw_material_code,
            group_code=group_code,
        )
        sql = f"""
        {self._base_ctes(max_depth=max_depth, include_test_products=include_test_products)}
            {filter_sql}
        )

        SELECT
            (SELECT COUNT(*) FROM CATALOG) AS total_exclusive_materials,
            (SELECT COUNT(DISTINCT finished_product_code) FROM CATALOG) AS total_finished_products_with_exclusive,
            (SELECT COUNT(*) FROM CATALOG) AS total_exclusive_links
        OPTION (MAXRECURSION 0);
        """
        params: list = [max_depth, *filter_params]
        with self as repo:
            row = repo.execute_one(sql, tuple(params)) or {}
        return row

    def fetch_exclusive_catalog_by_material(
        self,
        *,
        max_depth: int,
        limit: int,
        offset: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> list[dict]:
        filter_sql, filter_params = self._optional_filters(
            finished_product_code=finished_product_code,
            raw_material_code=raw_material_code,
            group_code=group_code,
        )
        sql = f"""
        {self._base_ctes(max_depth=max_depth, include_test_products=include_test_products)}
            {filter_sql}
        )

        SELECT
            raw_material_code,
            raw_material_description,
            raw_material_unit,
            raw_material_group,
            finished_product_code,
            finished_product_description,
            finished_product_unit
        FROM (
            SELECT
                C.*,
                ROW_NUMBER() OVER (
                    ORDER BY raw_material_code, finished_product_code
                ) AS _rn
            FROM CATALOG C
        ) ranked
        WHERE ranked._rn > ? AND ranked._rn <= ?
        ORDER BY ranked._rn
        OPTION (MAXRECURSION 0);
        """
        params: list = [max_depth, *filter_params, offset, offset + limit]
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))

    def fetch_exclusive_catalog_by_finished_product(
        self,
        *,
        max_depth: int,
        limit: int,
        offset: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> list[dict]:
        filter_sql, filter_params = self._optional_filters(
            finished_product_code=finished_product_code,
            raw_material_code=raw_material_code,
            group_code=group_code,
        )
        sql = f"""
        {self._base_ctes(max_depth=max_depth, include_test_products=include_test_products)}
            {filter_sql}
        ),

        PA_PAGE AS (
            SELECT
                finished_product_code,
                finished_product_description,
                finished_product_unit,
                COUNT(DISTINCT raw_material_code) AS exclusive_raw_material_count,
                ROW_NUMBER() OVER (ORDER BY finished_product_code) AS _pa_rn
            FROM CATALOG
            GROUP BY
                finished_product_code,
                finished_product_description,
                finished_product_unit
        )

        SELECT
            C.finished_product_code,
            C.finished_product_description,
            C.finished_product_unit,
            P.exclusive_raw_material_count,
            C.raw_material_code,
            C.raw_material_description,
            C.raw_material_unit,
            C.raw_material_group
        FROM PA_PAGE P
        INNER JOIN CATALOG C
            ON C.finished_product_code = P.finished_product_code
        WHERE P._pa_rn > ? AND P._pa_rn <= ?
        ORDER BY P.finished_product_code, C.raw_material_code
        OPTION (MAXRECURSION 0);
        """
        params: list = [max_depth, *filter_params, offset, offset + limit]
        with self as repo:
            return repo.execute_batch_query(sql, tuple(params))

"""SQL — intermediários compartilhados entre PAs com movimentação recente."""

from __future__ import annotations

from app.domain.production.shared_structure_intermediates_scope import (
    APPOINTMENTS_TABLE,
    MAX_BOM_DEPTH,
    PRODUCT_STRUCTURE_TABLE,
    PRODUCT_TABLE,
    VALID_BRANCHES,
)
from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_FINISHED_GOOD,
    PRODUCT_TYPE_INTERMEDIATE,
)

_ORDER_BEARING_TYPES = (PRODUCT_TYPE_INTERMEDIATE, PRODUCT_TYPE_FINISHED_GOOD)
_ORDER_BEARING_TYPES_SQL = ", ".join(f"'{item}'" for item in _ORDER_BEARING_TYPES)

_PAGE_ORDER_BY = "shared_pa_count DESC, component_code ASC"


def _branch_filter_sql(branch: str | None) -> tuple[str, list[str]]:
    if branch:
        return "H6.H6_FILIAL = ?", [branch]
    ordered = sorted(VALID_BRANCHES)
    placeholders = ", ".join("?" for _ in ordered)
    return f"H6.H6_FILIAL IN ({placeholders})", list(ordered)


def build_shared_intermediates_preamble(
    *,
    branch: str | None = None,
    movement_from: str,
    movement_to_exclusive: str,
) -> tuple[str, list]:
    """Materializa ``#ACTIVE_PA``, ``#PA_BOM`` e ``#SHARED``."""
    branch_sql, branch_params = _branch_filter_sql(branch)
    params: list = [*branch_params, movement_from, movement_to_exclusive, MAX_BOM_DEPTH]

    anchor_validity = ProductBomValidityFilterService.validity_filter_sql_for_today(
        alias="G1"
    )
    recursive_validity = ProductBomValidityFilterService.validity_filter_sql_for_today(
        alias="C"
    )

    sql = f"""
        SET NOCOUNT ON;
        DROP TABLE IF EXISTS #ACTIVE_PA;
        DROP TABLE IF EXISTS #PA_BOM;
        DROP TABLE IF EXISTS #SHARED;

        SELECT DISTINCT
            LTRIM(RTRIM(H6.H6_PRODUTO)) AS pa_code
        INTO #ACTIVE_PA
        FROM {APPOINTMENTS_TABLE} H6 WITH (NOLOCK)
        INNER JOIN {PRODUCT_TABLE} PA WITH (NOLOCK)
            ON PA.B1_COD = H6.H6_PRODUTO
           AND PA.D_E_L_E_T_ = ''
           AND PA.B1_TIPO = '{PRODUCT_TYPE_FINISHED_GOOD}'
           AND PA.B1_COD NOT LIKE '8000%'
           AND PA.B1_COD NOT LIKE '8001%'
        WHERE H6.D_E_L_E_T_ = ''
          AND H6.H6_TIPO = 'P'
          AND {branch_sql}
          AND H6.H6_DTAPONT >= ?
          AND H6.H6_DTAPONT < ?
          AND LTRIM(RTRIM(H6.H6_PRODUTO)) <> '';

        CREATE CLUSTERED INDEX IX_ACTIVE_PA ON #ACTIVE_PA (pa_code);

        WITH PA_LIST AS (
            SELECT pa_code FROM #ACTIVE_PA
        ), BOM_RAW AS (
            SELECT
                P.pa_code,
                G1.G1_COMP AS component_code,
                1 AS bom_level
            FROM PA_LIST P
            JOIN {PRODUCT_STRUCTURE_TABLE} G1 WITH (NOLOCK)
                ON G1.G1_COD = P.pa_code
               AND G1.D_E_L_E_T_ = ''{anchor_validity}
            UNION ALL
            SELECT
                B.pa_code,
                C.G1_COMP,
                B.bom_level + 1
            FROM BOM_RAW B
            JOIN {PRODUCT_STRUCTURE_TABLE} C WITH (NOLOCK)
                ON C.G1_COD = B.component_code
               AND C.D_E_L_E_T_ = ''{recursive_validity}
            WHERE B.bom_level < ?
        )
        SELECT
            BR.pa_code,
            BR.component_code,
            MIN(BR.bom_level) AS bom_level
        INTO #PA_BOM
        FROM BOM_RAW BR
        INNER JOIN {PRODUCT_TABLE} COMP WITH (NOLOCK)
            ON COMP.B1_COD = BR.component_code
           AND COMP.D_E_L_E_T_ = ''
           AND COMP.B1_TIPO IN ({_ORDER_BEARING_TYPES_SQL})
        WHERE BR.component_code <> BR.pa_code
        GROUP BY BR.pa_code, BR.component_code;

        CREATE CLUSTERED INDEX IX_PA_BOM ON #PA_BOM (component_code, pa_code);

        SELECT
            component_code,
            COUNT(DISTINCT pa_code) AS shared_pa_count
        INTO #SHARED
        FROM #PA_BOM
        GROUP BY component_code
        HAVING COUNT(DISTINCT pa_code) >= 2;

        CREATE CLUSTERED INDEX IX_SHARED ON #SHARED (component_code);
    """
    return sql, params


def build_shared_intermediates_summary_query(
    *,
    branch: str | None = None,
    movement_from: str,
    movement_to_exclusive: str,
) -> tuple[str, tuple]:
    preamble, params = build_shared_intermediates_preamble(
        branch=branch,
        movement_from=movement_from,
        movement_to_exclusive=movement_to_exclusive,
    )
    query = f"""
        {preamble}

        SELECT
            (SELECT COUNT(*) FROM #ACTIVE_PA) AS checked_pa_count,
            COUNT(*) AS shared_intermediate_count,
            ISNULL(MAX(S.shared_pa_count), 0) AS max_shared_pa_count
        FROM #SHARED S;
    """
    return query, tuple(params)


def build_shared_intermediates_query(
    *,
    offset: int,
    page_size: int,
    branch: str | None = None,
    movement_from: str,
    movement_to_exclusive: str,
) -> tuple[str, tuple]:
    """Uma linha por (intermediário, PA) dos intermediários da página."""
    preamble, params = build_shared_intermediates_preamble(
        branch=branch,
        movement_from=movement_from,
        movement_to_exclusive=movement_to_exclusive,
    )
    start = int(offset)
    end = int(offset) + int(page_size)
    params = [*params, start, end]

    query = f"""
        {preamble}

        WITH RANKED AS (
            SELECT
                S.component_code,
                S.shared_pa_count,
                ROW_NUMBER() OVER (ORDER BY {_PAGE_ORDER_BY}) AS item_rank
            FROM #SHARED S
        ), PAGE AS (
            SELECT component_code, shared_pa_count
            FROM RANKED
            WHERE item_rank > ? AND item_rank <= ?
        )
        SELECT
            LTRIM(RTRIM(PG.component_code)) AS component_code,
            LTRIM(RTRIM(ISNULL(IC.B1_DESC, ''))) AS component_description,
            LTRIM(RTRIM(ISNULL(IC.B1_TIPO, ''))) AS component_type,
            PG.shared_pa_count,
            LTRIM(RTRIM(B.pa_code)) AS pa_code,
            LTRIM(RTRIM(ISNULL(PA.B1_DESC, ''))) AS pa_description,
            B.bom_level
        FROM PAGE PG
        INNER JOIN #PA_BOM B
            ON B.component_code = PG.component_code
        LEFT JOIN {PRODUCT_TABLE} IC WITH (NOLOCK)
            ON IC.B1_COD = PG.component_code
           AND IC.D_E_L_E_T_ = ''
        LEFT JOIN {PRODUCT_TABLE} PA WITH (NOLOCK)
            ON PA.B1_COD = B.pa_code
           AND PA.D_E_L_E_T_ = ''
        ORDER BY PG.shared_pa_count DESC, PG.component_code ASC, B.pa_code ASC;
    """
    return query, tuple(params)

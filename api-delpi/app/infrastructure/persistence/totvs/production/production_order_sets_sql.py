"""SQL builders — conjuntos de ordens de produção incompletos (SC2010 x SG1010).

O diff compara, para cada conjunto com saldo em aberto, os componentes que a
estrutura do produto raiz **exigia** na emissão da OP mãe com os produtos que
**ganharam** OP filha. Falta = componente sem OP; sobra = OP de produto fora da
estrutura. Ver ``production_order_sets_scope`` para a sonda que fixou as regras.

As consultas são batches com tabelas temporárias, não uma CTE monolítica: o SQL
Server expande CTE inline e reavaliava a recursão da estrutura a cada
referência, o que levava a página de 1 s para 20 s (medido na filial 01).
"""

from __future__ import annotations

from app.domain.production.production_order_sets_scope import (
    MAX_BOM_DEPTH,
    PRODUCT_STRUCTURE_TABLE,
    PRODUCT_TABLE,
    PRODUCTION_ORDER_TABLE,
    PRODUCTION_ORDERS_VIEW,
    VALID_PRODUCTION_ORDER_SET_BRANCHES,
)
from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_FINISHED_GOOD,
    PRODUCT_TYPE_INTERMEDIATE,
)
from app.domain.totvs.protheus_production_orders import (
    MOTHER_ORDER_SEQUENCE,
    effective_due_date_sql,
)

# Só produto fabricado ganha OP própria; matéria-prima é consumida na operação.
_ORDER_BEARING_TYPES = (PRODUCT_TYPE_INTERMEDIATE, PRODUCT_TYPE_FINISHED_GOOD)
_ORDER_BEARING_TYPES_SQL = ", ".join(f"'{item}'" for item in _ORDER_BEARING_TYPES)

_DUE_DATE_EXPR = effective_due_date_sql(
    mother_due_date="V.DT_ENTREGA", order_due_date="SR.root_due_date"
)

# Entrega primeiro: o conjunto furado que vence antes é o que trava a fábrica.
# Sem entrega vai para o fim, como na carga máquina.
_PAGE_ORDER_BY = (
    "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC,"
    " set_number ASC, set_item ASC"
)


def _branch_filter_sql(branch: str | None) -> tuple[str, list[str]]:
    if branch:
        return "C2_FILIAL = ?", [branch]
    ordered = sorted(VALID_PRODUCTION_ORDER_SET_BRANCHES)
    placeholders = ", ".join("?" for _ in ordered)
    return f"C2_FILIAL IN ({placeholders})", list(ordered)


def build_diff_preamble(
    *,
    branch: str | None = None,
    issued_from: str | None = None,
) -> tuple[str, list]:
    """Batch que materializa ``#SET_ROOT``, ``#BOM`` e ``#DIFF``.

    ``issued_from`` (YYYYMMDD) recorta pela emissão da OP mãe. A filial 01 tem
    centenas de conjuntos abertos desde 2003 que nunca foram encerrados; sem o
    recorte a lista afoga o conjunto furado desta semana.
    """
    branch_sql, branch_params = _branch_filter_sql(branch)
    params: list = [*branch_params]

    issued_filter = ""
    if issued_from:
        issued_filter = (
            "\n           AND MIN(CASE WHEN OP.C2_SEQUEN = "
            f"'{MOTHER_ORDER_SEQUENCE}' THEN OP.C2_EMISSAO END) >= ?"
        )
        params.append(issued_from)
    params.append(MAX_BOM_DEPTH)

    anchor_validity = ProductBomValidityFilterService.validity_filter_sql(
        alias="G1", reference_param="R.reference_date"
    )
    recursive_validity = ProductBomValidityFilterService.validity_filter_sql(
        alias="C", reference_param="B.reference_date"
    )

    sql = f"""
        SET NOCOUNT ON;
        DROP TABLE IF EXISTS #SET_ROOT;
        DROP TABLE IF EXISTS #BOM;
        DROP TABLE IF EXISTS #DIFF;
        DROP TABLE IF EXISTS #PER_SET;

        SELECT
            OP.C2_FILIAL AS branch,
            OP.C2_NUM AS set_number,
            OP.C2_ITEM AS set_item,
            MIN(CASE WHEN OP.C2_SEQUEN = '{MOTHER_ORDER_SEQUENCE}'
                     THEN OP.C2_PRODUTO END) AS root_code,
            MIN(CASE WHEN OP.C2_SEQUEN = '{MOTHER_ORDER_SEQUENCE}'
                     THEN OP.C2_OP END) AS root_order_key,
            MIN(CASE WHEN OP.C2_SEQUEN = '{MOTHER_ORDER_SEQUENCE}'
                     THEN OP.C2_EMISSAO END) AS reference_date,
            MIN(CASE WHEN OP.C2_SEQUEN = '{MOTHER_ORDER_SEQUENCE}'
                     THEN OP.C2_DATPRF END) AS root_due_date,
            COUNT(*) AS order_count,
            SUM(CASE WHEN OP.C2_QUANT > OP.C2_QUJE THEN 1 ELSE 0 END) AS open_order_count
        INTO #SET_ROOT
        FROM {PRODUCTION_ORDER_TABLE} OP WITH (NOLOCK)
        JOIN (
            SELECT C2_FILIAL, C2_NUM, C2_ITEM
            FROM {PRODUCTION_ORDER_TABLE} WITH (NOLOCK)
            WHERE D_E_L_E_T_ = ''
              AND C2_QUANT > C2_QUJE
              AND {branch_sql}
            GROUP BY C2_FILIAL, C2_NUM, C2_ITEM
        ) S
            ON S.C2_FILIAL = OP.C2_FILIAL
           AND S.C2_NUM = OP.C2_NUM
           AND S.C2_ITEM = OP.C2_ITEM
        WHERE OP.D_E_L_E_T_ = ''
        GROUP BY OP.C2_FILIAL, OP.C2_NUM, OP.C2_ITEM
        HAVING MIN(CASE WHEN OP.C2_SEQUEN = '{MOTHER_ORDER_SEQUENCE}'
                        THEN OP.C2_PRODUTO END) IS NOT NULL{issued_filter};

        CREATE CLUSTERED INDEX IX_SET_ROOT ON #SET_ROOT (branch, set_number, set_item);

        WITH ROOT_REFS AS (
            SELECT DISTINCT root_code, reference_date FROM #SET_ROOT
        ), BOM_RAW AS (
            SELECT R.root_code, R.reference_date, G1.G1_COMP AS component_code, 1 AS bom_level
            FROM ROOT_REFS R
            JOIN {PRODUCT_STRUCTURE_TABLE} G1 WITH (NOLOCK)
                ON G1.G1_COD = R.root_code
               AND G1.D_E_L_E_T_ = ''{anchor_validity}
            UNION ALL
            SELECT B.root_code, B.reference_date, C.G1_COMP, B.bom_level + 1
            FROM BOM_RAW B
            JOIN {PRODUCT_STRUCTURE_TABLE} C WITH (NOLOCK)
                ON C.G1_COD = B.component_code
               AND C.D_E_L_E_T_ = ''{recursive_validity}
            WHERE B.bom_level < ?
        )
        SELECT root_code, reference_date, component_code, MIN(bom_level) AS bom_level
        INTO #BOM
        FROM BOM_RAW
        GROUP BY root_code, reference_date, component_code;

        CREATE CLUSTERED INDEX IX_BOM ON #BOM (root_code, reference_date);

        SELECT
            COALESCE(E.branch, A.branch) AS branch,
            COALESCE(E.set_number, A.set_number) AS set_number,
            COALESCE(E.set_item, A.set_item) AS set_item,
            COALESCE(E.component_code, A.component_code) AS component_code,
            E.bom_level,
            A.order_key,
            CASE WHEN A.component_code IS NULL THEN 1 ELSE 0 END AS is_missing,
            CASE WHEN E.component_code IS NULL THEN 1 ELSE 0 END AS is_extra
        INTO #DIFF
        FROM (
            SELECT SR.branch, SR.set_number, SR.set_item, B.component_code,
                   MIN(B.bom_level) AS bom_level
            FROM #SET_ROOT SR
            JOIN #BOM B
                ON B.root_code = SR.root_code
               AND B.reference_date = SR.reference_date
            JOIN {PRODUCT_TABLE} P WITH (NOLOCK)
                ON P.B1_COD = B.component_code
               AND P.D_E_L_E_T_ = ''
               AND P.B1_TIPO IN ({_ORDER_BEARING_TYPES_SQL})
            WHERE B.component_code <> SR.root_code
            GROUP BY SR.branch, SR.set_number, SR.set_item, B.component_code
        ) E
        FULL OUTER JOIN (
            SELECT
                OP.C2_FILIAL AS branch, OP.C2_NUM AS set_number, OP.C2_ITEM AS set_item,
                OP.C2_PRODUTO AS component_code, MIN(OP.C2_OP) AS order_key
            FROM #SET_ROOT SR
            JOIN {PRODUCTION_ORDER_TABLE} OP WITH (NOLOCK)
                ON OP.C2_FILIAL = SR.branch
               AND OP.C2_NUM = SR.set_number
               AND OP.C2_ITEM = SR.set_item
               AND OP.D_E_L_E_T_ = ''
               AND OP.C2_SEQUEN <> '{MOTHER_ORDER_SEQUENCE}'
            GROUP BY OP.C2_FILIAL, OP.C2_NUM, OP.C2_ITEM, OP.C2_PRODUTO
        ) A
            ON A.branch = E.branch
           AND A.set_number = E.set_number
           AND A.set_item = E.set_item
           AND A.component_code = E.component_code;

        CREATE CLUSTERED INDEX IX_DIFF ON #DIFF (branch, set_number, set_item);

        SELECT
            SR.branch, SR.set_number, SR.set_item,
            SR.root_code, SR.root_order_key, SR.reference_date, SR.root_due_date,
            SR.order_count, SR.open_order_count,
            SUM(CASE WHEN D.is_missing = 1 THEN 1 ELSE 0 END) AS missing_count,
            SUM(CASE WHEN D.is_extra = 1 THEN 1 ELSE 0 END) AS extra_count,
            SUM(CASE WHEN D.is_extra = 0 AND D.component_code IS NOT NULL THEN 1 ELSE 0 END)
                AS expected_component_count,
            SUM(CASE WHEN D.is_missing = 0 AND D.component_code IS NOT NULL THEN 1 ELSE 0 END)
                AS created_component_count
        INTO #PER_SET
        FROM #SET_ROOT SR
        LEFT JOIN #DIFF D
            ON D.branch = SR.branch
           AND D.set_number = SR.set_number
           AND D.set_item = SR.set_item
        GROUP BY
            SR.branch, SR.set_number, SR.set_item,
            SR.root_code, SR.root_order_key, SR.reference_date, SR.root_due_date,
            SR.order_count, SR.open_order_count;
    """
    return sql, params


def build_incomplete_sets_summary_query(
    *,
    branch: str | None = None,
    issued_from: str | None = None,
) -> tuple[str, tuple]:
    """Contagem do universo e dos conjuntos com problema — alimenta o card."""
    preamble, params = build_diff_preamble(branch=branch, issued_from=issued_from)
    query = f"""
        {preamble}

        SELECT
            COUNT(*) AS checked_set_count,
            SUM(CASE WHEN missing_count > 0 OR extra_count > 0 THEN 1 ELSE 0 END)
                AS incomplete_set_count,
            SUM(CASE WHEN missing_count > 0 THEN 1 ELSE 0 END) AS missing_set_count,
            SUM(CASE WHEN extra_count > 0 THEN 1 ELSE 0 END) AS extra_set_count
        FROM #PER_SET;
    """
    return query, tuple(params)


def build_incomplete_sets_query(
    *,
    offset: int,
    page_size: int,
    branch: str | None = None,
    issued_from: str | None = None,
) -> tuple[str, tuple]:
    """Uma linha por (conjunto, componente divergente) da página pedida.

    A paginação é por **conjunto** (``ROW_NUMBER`` sobre os conjuntos furados);
    os componentes vêm junto para o mapper agrupar sem uma segunda ida ao banco.
    """
    preamble, params = build_diff_preamble(branch=branch, issued_from=issued_from)
    query = f"""
        {preamble}

        WITH INCOMPLETE AS (
            SELECT
                SR.*,
                {_DUE_DATE_EXPR} AS due_date
            FROM #PER_SET SR
            LEFT JOIN {PRODUCTION_ORDERS_VIEW} V WITH (NOLOCK)
                ON V.FILIAL = SR.branch
               AND V.OP_CHAVE = SR.root_order_key
            WHERE SR.missing_count > 0 OR SR.extra_count > 0
        ), PAGE AS (
            SELECT *, ROW_NUMBER() OVER (ORDER BY {_PAGE_ORDER_BY}) AS set_rank
            FROM INCOMPLETE
        )
        SELECT
            LTRIM(RTRIM(PG.branch)) AS branch,
            LTRIM(RTRIM(PG.set_number)) AS set_number,
            LTRIM(RTRIM(PG.set_item)) AS set_item,
            LTRIM(RTRIM(PG.root_code)) AS root_code,
            LTRIM(RTRIM(ISNULL(RP.B1_DESC, ''))) AS root_description,
            LTRIM(RTRIM(ISNULL(RP.B1_TIPO, ''))) AS root_type,
            LTRIM(RTRIM(PG.root_order_key)) AS root_order_key,
            PG.due_date AS due_date,
            PG.reference_date AS reference_date,
            PG.order_count AS order_count,
            PG.open_order_count AS open_order_count,
            PG.expected_component_count AS expected_component_count,
            PG.created_component_count AS created_component_count,
            PG.missing_count AS missing_count,
            PG.extra_count AS extra_count,
            LTRIM(RTRIM(ISNULL(D.component_code, ''))) AS component_code,
            LTRIM(RTRIM(ISNULL(CP.B1_DESC, ''))) AS component_description,
            LTRIM(RTRIM(ISNULL(CP.B1_TIPO, ''))) AS component_type,
            ISNULL(D.bom_level, 0) AS bom_level,
            LTRIM(RTRIM(ISNULL(D.order_key, ''))) AS component_order_key,
            ISNULL(D.is_missing, 0) AS is_missing,
            ISNULL(D.is_extra, 0) AS is_extra,
            PG.set_rank AS set_rank
        FROM PAGE PG
        LEFT JOIN {PRODUCT_TABLE} RP WITH (NOLOCK)
            ON RP.B1_COD = PG.root_code
           AND RP.D_E_L_E_T_ = ''
        LEFT JOIN #DIFF D
            ON D.branch = PG.branch
           AND D.set_number = PG.set_number
           AND D.set_item = PG.set_item
           AND (D.is_missing = 1 OR D.is_extra = 1)
        LEFT JOIN {PRODUCT_TABLE} CP WITH (NOLOCK)
            ON CP.B1_COD = D.component_code
           AND CP.D_E_L_E_T_ = ''
        WHERE PG.set_rank > ? AND PG.set_rank <= ?
        ORDER BY PG.set_rank ASC, D.is_missing DESC, D.component_code ASC;
    """
    return query, (*params, offset, offset + page_size)

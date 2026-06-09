"""Montagem canônica das CTEs de apontamento no CT de inspeção final (PPM)."""

from dataclasses import dataclass

from app.domain.services.ppm_inspection_denominator import CT_INSPECAO_NOME_SQL_LIKE
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_production_sql import (
    APONT_INSPECAO_CTE,
    CT_INSPECAO_FINAL_CTE,
    CT_INSPECAO_JOIN,
    QTD_PRODUZIDA_OP_EXPR,
    SH1_RECURSO_JOIN,
)


@dataclass(frozen=True, slots=True)
class InspectionApontCteBundle:
    ct_inspecao_cte: str
    apont_inspecao_cte: str
    params: list[str]


def build_inspection_apont_ctes(
    *,
    branch: str | None = None,
    product_codes: list[str] | None = None,
) -> InspectionApontCteBundle:
    prod_branch_filter_ct = ""
    prod_branch_filter_sh6 = ""
    params: list[str] = []

    if branch:
        prod_branch_filter_ct = "AND HB.HB_FILIAL = ?"
        prod_branch_filter_sh6 = "AND SH6.H6_FILIAL = ?"
        params.extend([branch, branch])

    product_filter = ""
    if product_codes:
        placeholders = ", ".join("?" for _ in product_codes)
        product_filter = f"AND SH6.H6_PRODUTO IN ({placeholders})"
        params.extend(product_codes)

    ct_inspecao_cte = CT_INSPECAO_FINAL_CTE.format(
        ct_branch_filter=prod_branch_filter_ct,
    )
    apont_inspecao_cte = APONT_INSPECAO_CTE.format(
        qtd_expr=QTD_PRODUZIDA_OP_EXPR.strip(),
        sh1_join=SH1_RECURSO_JOIN.strip(),
        ct_join=CT_INSPECAO_JOIN.strip(),
        sh6_branch_filter=prod_branch_filter_sh6,
        product_filter=product_filter,
    )
    return InspectionApontCteBundle(
        ct_inspecao_cte=ct_inspecao_cte,
        apont_inspecao_cte=apont_inspecao_cte,
        params=params,
    )


def append_apont_date_params(
    params: list[str],
    *,
    date_start: str | None,
    date_end_exclusive: str | None,
) -> list[str]:
    extended = list(params)
    extended.extend([date_start, date_end_exclusive])
    return extended


SQL_LIST_INSPECTION_CTS = f"""
SELECT HB_FILIAL, HB_COD, HB_NOME
FROM SHB010
WHERE D_E_L_E_T_ = ' '
  AND UPPER(HB_NOME) LIKE '{CT_INSPECAO_NOME_SQL_LIKE}'
ORDER BY HB_FILIAL, HB_COD
"""


def sql_produced_totals_by_tipo(*, branch: str) -> tuple[str, tuple[str, ...]]:
    bundle = build_inspection_apont_ctes(branch=branch)
    sql = f"""
        WITH
        {bundle.ct_inspecao_cte.strip()},
        {bundle.apont_inspecao_cte.strip()}
        SELECT
            B1_TIPO,
            SUM(qtd_produzida_op) * 1000 AS total_un
        FROM apont_inspecao
        GROUP BY B1_TIPO
    """
    # branch twice in bundle + date_start + date_end_exclusive filled by caller
    return sql, tuple(bundle.params)

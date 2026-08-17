"""SQL analítico — datas distintas de ocorrência QI2 (numerador do streak de NC)."""

from __future__ import annotations

from app.domain.services.quality.nonconformity_query_filter_service import (
    qi2_tipo_codes_for_filter,
)
from app.domain.totvs.protheus_branches import is_all_branches, normalize_branch_scope
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_OCCURRENCE_DATE_SQL = (
    "TRY_CONVERT(date, NULLIF(LTRIM(RTRIM(QI2_OCORRE)), ''), 112)"
)


def build_occurrence_dates_query(
    *,
    filter_type: str,
    branch: str | None = None,
    product_prefix: str | None = None,
) -> tuple[str, tuple]:
    """Lista datas distintas de ``QI2_OCORRE`` (mesmo recorte da listagem/série de NC)."""
    qb = QueryBuilder()
    qb.raw("D_E_L_E_T_ = ''")

    type_codes = qi2_tipo_codes_for_filter(filter_type)
    if type_codes:
        qb.in_list("QI2_TIPO", type_codes)

    if branch and not is_all_branches(branch):
        qb.eq("QI2_FILIAL", normalize_branch_scope(branch))

    qb.raw(f"{_OCCURRENCE_DATE_SQL} IS NOT NULL")
    where, params = qb.build()

    if product_prefix:
        where = f"{where} AND QI2_ITEM LIKE ?"
        params = tuple(list(params) + [f"{product_prefix}%"])

    sql = f"""
        SELECT DISTINCT
            {_OCCURRENCE_DATE_SQL} AS occurrence_date
        FROM QI2010 WITH (NOLOCK)
        WHERE {where}
        ORDER BY occurrence_date
    """
    return sql, tuple(params)

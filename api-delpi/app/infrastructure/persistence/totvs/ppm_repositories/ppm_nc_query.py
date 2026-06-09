"""Helpers de query para não conformidades (numerador PPM)."""

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def build_nc_where_clause(
    *,
    ppm_type: str,
    branch: str | None,
    date_start: str | None,
    date_end_exclusive: str | None,
) -> tuple[str, list]:
    if ppm_type == "internal":
        type_filter = "QI2_TIPO = '1'"
    elif ppm_type == "external":
        type_filter = "QI2_TIPO = '2'"
    else:
        raise ValueError("ppm_type deve ser internal ou external")

    qb = QueryBuilder()
    qb.raw("D_E_L_E_T_ = ' '")

    if branch:
        qb.eq("QI2_FILIAL", branch)

    if date_start:
        qb.gte("QI2_OCORRE", date_start)

    if date_end_exclusive:
        qb.lt("QI2_OCORRE", date_end_exclusive)

    qb.raw(type_filter)
    return qb.build()

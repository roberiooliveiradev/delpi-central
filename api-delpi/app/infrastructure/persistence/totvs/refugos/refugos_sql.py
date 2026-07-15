"""SQL builders — Acompanhamento de Refugos (SBC010 + joins).

ValorPerda (Fase 0 validada):
  BC_QUANT * COALESCE(NULLIF(AVG(B2_CM1), 0), NULLIF(B1_CUSTD, 0), 0)

Join SB2 agregado por filial+produto evita multiplicação por B2_LOCAL.
"""

from __future__ import annotations

from app.domain.quality.refugos.refugos_scope import REFUGOS_LOSS_TYPE
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    MAX_FILTROS_ITEMS,
    RANKING_DIMENSIONS,
)

# Custo médio sem multiplicar linhas (vários B2_LOCAL).
_COST_JOIN = """
LEFT JOIN (
    SELECT
        B2_FILIAL,
        B2_COD,
        AVG(NULLIF(CAST(B2_CM1 AS FLOAT), 0)) AS AVG_CM1
    FROM SB2010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
    GROUP BY B2_FILIAL, B2_COD
) CM
    ON CM.B2_FILIAL = BC.BC_FILIAL
   AND CM.B2_COD = BC.BC_PRODUTO
"""

_VALOR_EXPR = (
    "BC.BC_QUANT * COALESCE(NULLIF(CM.AVG_CM1, 0), "
    "NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0)"
)

_UNIT_COST_EXPR = (
    "COALESCE(NULLIF(CM.AVG_CM1, 0), NULLIF(CAST(SB1.B1_CUSTD AS FLOAT), 0), 0)"
)

_BASE_FROM = f"""
FROM SBC010 BC WITH (NOLOCK)
INNER JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = BC.BC_PRODUTO
   AND SB1.D_E_L_E_T_ = ''
{_COST_JOIN}
LEFT JOIN SC2010 OP WITH (NOLOCK)
    ON OP.C2_FILIAL = BC.BC_FILIAL
   AND OP.C2_OP = BC.BC_OP
   AND OP.D_E_L_E_T_ = ''
LEFT JOIN CYO010 CYO WITH (NOLOCK)
    ON CYO.CYO_CDRF = BC.BC_MOTIVO
   AND CYO.D_E_L_E_T_ = ''
LEFT JOIN SYS_USR U WITH (NOLOCK)
    ON U.USR_ID = BC.BC_OPERADO
LEFT JOIN SB1010 PA1 WITH (NOLOCK)
    ON PA1.B1_COD = OP.C2_PRODUTO
   AND PA1.D_E_L_E_T_ = ''
"""


def build_base_where(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    mp: str | None = None,
    pa: str | None = None,
    op: str | None = None,
    motivo: str | None = None,
    recurso: str | None = None,
) -> tuple[str, list]:
    clauses = [
        "BC.D_E_L_E_T_ = ''",
        "BC.BC_TIPO = ?",
        "LTRIM(RTRIM(BC.BC_FILIAL)) = ?",
        "BC.BC_DATA >= ?",
        "BC.BC_DATA < ?",
    ]
    params: list = [REFUGOS_LOSS_TYPE, branch, date_start, date_end_exclusive]

    if mp:
        clauses.append("LTRIM(RTRIM(BC.BC_PRODUTO)) = ?")
        params.append(mp)
    if pa:
        clauses.append("LTRIM(RTRIM(OP.C2_PRODUTO)) = ?")
        params.append(pa)
    if op:
        clauses.append("LTRIM(RTRIM(BC.BC_OP)) = ?")
        params.append(op)
    if motivo:
        clauses.append("LTRIM(RTRIM(BC.BC_MOTIVO)) = ?")
        params.append(motivo)
    if recurso:
        clauses.append("LTRIM(RTRIM(BC.BC_RECURSO)) = ?")
        params.append(recurso)

    return " AND ".join(clauses), params


def build_health_query() -> tuple[str, tuple]:
    return (
        """
        SELECT TOP 1
            LTRIM(RTRIM(BC.BC_FILIAL)) AS filial,
            BC.BC_DATA AS ultima_data
        FROM SBC010 BC WITH (NOLOCK)
        WHERE BC.D_E_L_E_T_ = ''
          AND BC.BC_TIPO = ?
        ORDER BY BC.BC_DATA DESC
        """,
        (REFUGOS_LOSS_TYPE,),
    )


def build_filtros_mp_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(BC.BC_PRODUTO)) AS codigo,
            LTRIM(RTRIM(SB1.B1_DESC)) AS descricao
        {_BASE_FROM}
        WHERE {where}
          AND LTRIM(RTRIM(BC.BC_PRODUTO)) <> ''
        GROUP BY LTRIM(RTRIM(BC.BC_PRODUTO)), LTRIM(RTRIM(SB1.B1_DESC))
        ORDER BY codigo
        """,
        tuple(params),
    )


def build_filtros_pa_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(OP.C2_PRODUTO)) AS codigo,
            LTRIM(RTRIM(PA1.B1_DESC)) AS descricao
        {_BASE_FROM}
        WHERE {where}
          AND LTRIM(RTRIM(OP.C2_PRODUTO)) <> ''
        GROUP BY LTRIM(RTRIM(OP.C2_PRODUTO)), LTRIM(RTRIM(PA1.B1_DESC))
        ORDER BY codigo
        """,
        tuple(params),
    )


def build_filtros_op_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(BC.BC_OP)) AS codigo
        {_BASE_FROM}
        WHERE {where}
          AND LTRIM(RTRIM(BC.BC_OP)) <> ''
        GROUP BY LTRIM(RTRIM(BC.BC_OP))
        ORDER BY codigo
        """,
        tuple(params),
    )


def build_filtros_motivo_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(BC.BC_MOTIVO)) AS codigo,
            LTRIM(RTRIM(CYO.CYO_DSRF)) AS descricao
        {_BASE_FROM}
        WHERE {where}
          AND LTRIM(RTRIM(BC.BC_MOTIVO)) <> ''
        GROUP BY LTRIM(RTRIM(BC.BC_MOTIVO)), LTRIM(RTRIM(CYO.CYO_DSRF))
        ORDER BY codigo
        """,
        tuple(params),
    )


def build_resumo_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    day_start: str,
    day_end_exclusive: str,
    month_start: str,
    month_end_exclusive: str,
    mp: str | None = None,
    pa: str | None = None,
    op: str | None = None,
    motivo: str | None = None,
    recurso: str | None = None,
) -> tuple[str, tuple]:
    """Uma query: total do período + KPIs do dia (dataFim) e do mês calendário completo de dataFim."""
    sql = f"""
    SELECT
        SUM(CASE WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ? THEN {_VALOR_EXPR} ELSE 0 END) AS total_valor,
        SUM(CASE WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ? THEN BC.BC_QUANT ELSE 0 END) AS total_quantidade,
        SUM(CASE WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ? THEN 1 ELSE 0 END) AS ocorrencias,
        SUM(
            CASE
                WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ?
                     AND {_UNIT_COST_EXPR} = 0 THEN 1
                ELSE 0
            END
        ) AS registros_sem_custo,
        SUM(CASE WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ? THEN {_VALOR_EXPR} ELSE 0 END) AS valor_dia,
        SUM(CASE WHEN BC.BC_DATA >= ? AND BC.BC_DATA < ? THEN {_VALOR_EXPR} ELSE 0 END) AS valor_mes
    {_BASE_FROM}
    WHERE BC.D_E_L_E_T_ = ''
      AND BC.BC_TIPO = ?
      AND LTRIM(RTRIM(BC.BC_FILIAL)) = ?
      AND BC.BC_DATA >= ?
      AND BC.BC_DATA < ?
    """
    params: list = [
        date_start,
        date_end_exclusive,
        date_start,
        date_end_exclusive,
        date_start,
        date_end_exclusive,
        date_start,
        date_end_exclusive,
        day_start,
        day_end_exclusive,
        month_start,
        month_end_exclusive,
        REFUGOS_LOSS_TYPE,
        branch,
        min(date_start, day_start, month_start),
        max(date_end_exclusive, day_end_exclusive, month_end_exclusive),
    ]

    extras: list[str] = []
    if mp:
        extras.append("AND LTRIM(RTRIM(BC.BC_PRODUTO)) = ?")
        params.append(mp)
    if pa:
        extras.append("AND LTRIM(RTRIM(OP.C2_PRODUTO)) = ?")
        params.append(pa)
    if op:
        extras.append("AND LTRIM(RTRIM(BC.BC_OP)) = ?")
        params.append(op)
    if motivo:
        extras.append("AND LTRIM(RTRIM(BC.BC_MOTIVO)) = ?")
        params.append(motivo)
    if recurso:
        extras.append("AND LTRIM(RTRIM(BC.BC_RECURSO)) = ?")
        params.append(recurso)

    if extras:
        sql = sql.rstrip() + "\n      " + "\n      ".join(extras)

    return sql, tuple(params)


def build_ranking_query(
    *,
    dimension: str,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    limit: int,
    mp: str | None = None,
    pa: str | None = None,
    op: str | None = None,
    motivo: str | None = None,
    recurso: str | None = None,
) -> tuple[str, tuple]:
    if dimension not in RANKING_DIMENSIONS:
        raise ValueError(f"dimension inválida: {dimension}")

    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
    )

    dim_map = {
        "motivo": (
            "LTRIM(RTRIM(BC.BC_MOTIVO))",
            "LTRIM(RTRIM(CYO.CYO_DSRF))",
        ),
        "materia_prima": (
            "LTRIM(RTRIM(BC.BC_PRODUTO))",
            "LTRIM(RTRIM(SB1.B1_DESC))",
        ),
        "produto_acabado": (
            "LTRIM(RTRIM(OP.C2_PRODUTO))",
            "LTRIM(RTRIM(PA1.B1_DESC))",
        ),
        "centro_trabalho": (
            "LTRIM(RTRIM(BC.BC_RECURSO))",
            "LTRIM(RTRIM(BC.BC_RECURSO))",
        ),
        "colaborador": (
            "LTRIM(RTRIM(BC.BC_OPERADO))",
            "LTRIM(RTRIM(U.USR_NOME))",
        ),
    }
    code_expr, label_expr = dim_map[dimension]

    sql = f"""
    SELECT TOP {int(limit)}
        {code_expr} AS code,
        {label_expr} AS label,
        SUM(BC.BC_QUANT) AS quantity,
        SUM({_VALOR_EXPR}) AS value,
        COUNT(*) AS occurrence_count
    {_BASE_FROM}
    WHERE {where}
      AND {code_expr} IS NOT NULL
      AND {code_expr} <> ''
    GROUP BY {code_expr}, {label_expr}
    ORDER BY value DESC, code ASC
    """
    return sql, tuple(params)


def build_registros_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    offset: int,
    page_size: int,
    mp: str | None = None,
    pa: str | None = None,
    op: str | None = None,
    motivo: str | None = None,
    recurso: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
    )
    # SQL Server OFFSET/FETCH
    sql = f"""
    SELECT
        LTRIM(RTRIM(BC.BC_FILIAL)) AS filial,
        BC.BC_DATA AS loss_date,
        LTRIM(RTRIM(BC.BC_OP)) AS production_order,
        LTRIM(RTRIM(OP.C2_PRODUTO)) AS finished_product,
        LTRIM(RTRIM(BC.BC_PRODUTO)) AS material_code,
        LTRIM(RTRIM(SB1.B1_DESC)) AS description,
        LTRIM(RTRIM(SB1.B1_UM)) AS unit,
        LTRIM(RTRIM(BC.BC_MOTIVO)) AS reason_code,
        LTRIM(RTRIM(CYO.CYO_DSRF)) AS reason_label,
        BC.BC_QUANT AS quantity,
        {_VALOR_EXPR} AS value,
        LTRIM(RTRIM(BC.BC_RECURSO)) AS work_center,
        LTRIM(RTRIM(BC.BC_OPERADO)) AS operator_id,
        LTRIM(RTRIM(U.USR_NOME)) AS operator_name
    {_BASE_FROM}
    WHERE {where}
    ORDER BY BC.BC_DATA DESC, {_VALOR_EXPR} DESC, BC.BC_PRODUTO ASC
    OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY
    """
    return sql, tuple(params)


def build_registros_count_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    mp: str | None = None,
    pa: str | None = None,
    op: str | None = None,
    motivo: str | None = None,
    recurso: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_base_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        mp=mp,
        pa=pa,
        op=op,
        motivo=motivo,
        recurso=recurso,
    )
    sql = f"""
    SELECT COUNT(*) AS total
    {_BASE_FROM}
    WHERE {where}
    """
    return sql, tuple(params)

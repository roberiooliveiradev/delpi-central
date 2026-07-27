"""Listagem eficiência fabril com appointment_id (mesmo vínculo SH6010 do OEE)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import EFICIENCIA_FABRIL_VIEW
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    FINISHED_PRODUCTION_ORDER_SUFFIX,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    FABRIL_SH6010_OUTER_APPLY,
)

# PA via OP mãe (mesmo padrão estoque-segurança / machine programs):
# LEFT(OP, 6) + '01001' → SC2.C2_PRODUTO
_FINISHED_OP_FROM_EF = (
    f"LEFT(RTRIM(EF.OP), 6) + '{FINISHED_PRODUCTION_ORDER_SUFFIX}'"
)

# Meta/hora = ritmo padrão (sem setup), mesma base da parte variável do previsto:
# QTD_TOTAL_OP / COALESCE(HY_TEMPOM, G2_TEMPAD/1000)
# Unidade = mesma de QTD_APONTADA / C2_QUANT (ex.: MI/h).
_STANDARD_TIME_FACTOR_SQL = """
COALESCE(
    SHY.HY_TEMPOM,
    CASE
        WHEN SG2.G2_TEMPAD IS NOT NULL AND SG2.G2_TEMPAD > 0
        THEN SG2.G2_TEMPAD / 1000.0
        ELSE NULL
    END
)
"""

_META_POR_HORA_SQL = f"""
CASE
    WHEN NULLIF(TRY_CAST(EF.QTD_TOTAL_OP AS FLOAT), 0) IS NOT NULL
     AND NULLIF(({_STANDARD_TIME_FACTOR_SQL}), 0) IS NOT NULL
    THEN ROUND(
        TRY_CAST(EF.QTD_TOTAL_OP AS FLOAT) / ({_STANDARD_TIME_FACTOR_SQL}),
        6
    )
    ELSE NULL
END
"""

EF_FABRIL_ITEMS_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{FABRIL_SH6010_OUTER_APPLY}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""

EF_FABRIL_ITEMS_SELECT = f"""
    H6.appointment_id AS appointment_id,
    RTRIM(LTRIM(EF.FILIAL)) AS FILIAL,
    RTRIM(LTRIM(EF.OP)) AS OP,
    RTRIM(LTRIM(EF.PRODUTO)) AS PRODUTO,
    RTRIM(LTRIM(COALESCE(FP.PRODUTO_ACABADO, ''))) AS PRODUTO_ACABADO,
    RTRIM(LTRIM(EF.DESCRICAO_PRODUTO)) AS DESCRICAO_PRODUTO,
    RTRIM(LTRIM(SB1.B1_UM)) AS UNIDADE,
    RTRIM(LTRIM(EF.CENTRO_TRABALHO)) AS CENTRO_TRABALHO,
    RTRIM(LTRIM(EF.OPERACAO)) AS OPERACAO,
    RTRIM(LTRIM(COALESCE(SG2.DESCRICAO_OPERACAO, ''))) AS DESCRICAO_OPERACAO,
    RTRIM(LTRIM(EF.COD_OPERADOR)) AS COD_OPERADOR,
    RTRIM(LTRIM(EF.LOGIN_OPERADOR)) AS LOGIN_OPERADOR,
    RTRIM(LTRIM(EF.NOME_OPERADOR)) AS NOME_OPERADOR,
    EF.DATA_PRODUCAO AS DATA_PRODUCAO,
    RTRIM(LTRIM(EF.HORA_INICIO)) AS HORA_INICIO,
    RTRIM(LTRIM(EF.HORA_FINAL)) AS HORA_FINAL,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS QTD_APONTADA,
    {_META_POR_HORA_SQL} AS META_POR_HORA,
    TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT) AS TEMPO_REAL_HORAS,
    TRY_CAST(EF.TEMPO_PREVISTO_HORAS AS FLOAT) AS TEMPO_PREVISTO_HORAS,
    TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT) AS EFICIENCIA_PERCENTUAL,
    TRY_CAST(EF.VALOR_MOD_HORA AS FLOAT) AS VALOR_MOD_HORA,
    TRY_CAST(EF.TEMPO_GANHO_PERDIDO_HORAS AS FLOAT) AS TEMPO_GANHO_PERDIDO_HORAS,
    TRY_CAST(EF.RESULTADO_MOD AS FLOAT) AS RESULTADO_MOD,
    TRY_CAST(EF.LUCRO_MOD AS FLOAT) AS LUCRO_MOD,
    TRY_CAST(EF.PREJUIZO_MOD AS FLOAT) AS PREJUIZO_MOD,
    RTRIM(LTRIM(EF.STATUS_RESULTADO_MOD)) AS STATUS_RESULTADO_MOD,
    RTRIM(LTRIM(EF.STATUS_REGISTRO)) AS STATUS_REGISTRO
"""

EF_FABRIL_ITEMS_LIST_SELECT = f"""
    H6.appointment_id AS appointment_id,
    EF.FILIAL AS FILIAL,
    EF.OP AS OP,
    EF.PRODUTO AS PRODUTO,
    RTRIM(LTRIM(COALESCE(FP.PRODUTO_ACABADO, ''))) AS PRODUTO_ACABADO,
    EF.DESCRICAO_PRODUTO AS DESCRICAO_PRODUTO,
    RTRIM(LTRIM(SB1.B1_UM)) AS UNIDADE,
    EF.CENTRO_TRABALHO AS CENTRO_TRABALHO,
    EF.OPERACAO AS OPERACAO,
    RTRIM(LTRIM(COALESCE(SG2.DESCRICAO_OPERACAO, ''))) AS DESCRICAO_OPERACAO,
    EF.COD_OPERADOR AS COD_OPERADOR,
    EF.LOGIN_OPERADOR AS LOGIN_OPERADOR,
    EF.NOME_OPERADOR AS NOME_OPERADOR,
    EF.DATA_PRODUCAO AS DATA_PRODUCAO,
    EF.HORA_INICIO AS HORA_INICIO,
    EF.HORA_FINAL AS HORA_FINAL,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS QTD_APONTADA,
    {_META_POR_HORA_SQL} AS META_POR_HORA,
    TRY_CAST(EF.TEMPO_REAL_HORAS AS FLOAT) AS TEMPO_REAL_HORAS,
    TRY_CAST(EF.TEMPO_PREVISTO_HORAS AS FLOAT) AS TEMPO_PREVISTO_HORAS,
    TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS FLOAT) AS EFICIENCIA_PERCENTUAL,
    TRY_CAST(EF.VALOR_MOD_HORA AS FLOAT) AS VALOR_MOD_HORA,
    TRY_CAST(EF.TEMPO_GANHO_PERDIDO_HORAS AS FLOAT) AS TEMPO_GANHO_PERDIDO_HORAS,
    TRY_CAST(EF.RESULTADO_MOD AS FLOAT) AS RESULTADO_MOD,
    TRY_CAST(EF.LUCRO_MOD AS FLOAT) AS LUCRO_MOD,
    TRY_CAST(EF.PREJUIZO_MOD AS FLOAT) AS PREJUIZO_MOD,
    EF.STATUS_RESULTADO_MOD AS STATUS_RESULTADO_MOD,
    EF.STATUS_REGISTRO AS STATUS_REGISTRO
"""

H6_RANKED_JOIN = """
LEFT JOIN H6_RANKED H6
    ON H6.rn = 1
   AND H6.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND H6.match_op = RTRIM(LTRIM(EF.OP))
   AND H6.match_data_producao = EF.DATA_PRODUCAO
   AND H6.match_hora_inicio = RTRIM(LTRIM(ISNULL(EF.HORA_INICIO, '')))
   AND H6.match_hora_final = RTRIM(LTRIM(ISNULL(EF.HORA_FINAL, '')))
   AND H6.match_operacao = RTRIM(LTRIM(EF.OPERACAO))
"""

# Joins set-based (CTEs ranqueadas) — evita OUTER APPLY correlacionado por linha.
EF_FABRIL_PA_AND_OPERATION_JOINS = f"""
LEFT JOIN PA_RANKED FP
    ON FP.rn = 1
   AND FP.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND LEN(RTRIM(EF.OP)) >= 6
   AND FP.match_finished_op = {_FINISHED_OP_FROM_EF}
LEFT JOIN SHY_RANKED SHY
    ON SHY.rn = 1
   AND SHY.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND SHY.match_op = RTRIM(LTRIM(EF.OP))
   AND SHY.match_operacao = RTRIM(LTRIM(EF.OPERACAO))
LEFT JOIN SG2_RANKED SG2
    ON SG2.rn = 1
   AND SG2.match_filial = RTRIM(LTRIM(EF.FILIAL))
   AND SG2.match_produto = RTRIM(LTRIM(EF.PRODUTO))
   AND SG2.match_operacao = RTRIM(LTRIM(EF.OPERACAO))
"""


def _branch_filter_sql(
    *,
    column_sql: str,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, list]:
    params: list = []
    if branch:
        return f"AND {column_sql} = ?", [branch]
    placeholders = ", ".join("?" for _ in branches)
    params.extend(branches)
    return f"AND {column_sql} IN ({placeholders})", params


def build_fabril_sh6010_ranked_cte(
    *,
    date_start: str,
    date_end: str,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, tuple]:
    """Uma varredura em SH6010 por período (evita OUTER APPLY correlacionado em bulk)."""
    params: list = [date_start, date_end]
    branch_filter, branch_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(H6.H6_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(branch_params)

    cte = f"""
H6_RANKED AS (
    SELECT
        CAST(H6.R_E_C_N_O_ AS BIGINT) AS appointment_id,
        RTRIM(LTRIM(H6.H6_FILIAL)) AS match_filial,
        RTRIM(LTRIM(H6.H6_OP)) AS match_op,
        CONVERT(DATE, H6.H6_DTPROD, 112) AS match_data_producao,
        RTRIM(LTRIM(ISNULL(H6.H6_HORAINI, ''))) AS match_hora_inicio,
        RTRIM(LTRIM(ISNULL(H6.H6_HORAFIN, ''))) AS match_hora_final,
        RTRIM(LTRIM(H6.H6_OPERAC)) AS match_operacao,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(H6.H6_FILIAL)),
                RTRIM(LTRIM(H6.H6_OP)),
                CONVERT(DATE, H6.H6_DTPROD, 112),
                RTRIM(LTRIM(ISNULL(H6.H6_HORAINI, ''))),
                RTRIM(LTRIM(ISNULL(H6.H6_HORAFIN, ''))),
                RTRIM(LTRIM(H6.H6_OPERAC))
            ORDER BY H6.R_E_C_N_O_ DESC
        ) AS rn
    FROM SH6010 H6 WITH (NOLOCK)
    WHERE H6.D_E_L_E_T_ = ''
      AND CONVERT(DATE, H6.H6_DTPROD, 112) >= ?
      AND CONVERT(DATE, H6.H6_DTPROD, 112) <= ?
      {branch_filter}
)"""
    return cte, tuple(params)


def build_fabril_pa_and_operation_ranked_ctes(
    *,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, tuple]:
    """CTEs set-based: PA (SC2 mãe), tempo padrão OP (SHY) e roteiro (SG2)."""
    params: list = []
    pa_branch_filter, pa_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(FP.C2_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(pa_params)
    shy_branch_filter, shy_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(SHY.HY_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(shy_params)
    sg2_branch_filter, sg2_params = _branch_filter_sql(
        column_sql="RTRIM(LTRIM(SG2.G2_FILIAL))",
        branch=branch,
        branches=branches,
    )
    params.extend(sg2_params)

    cte = f"""
PA_RANKED AS (
    SELECT
        RTRIM(LTRIM(FP.C2_FILIAL)) AS match_filial,
        RTRIM(LTRIM(FP.C2_OP)) AS match_finished_op,
        RTRIM(LTRIM(FP.C2_PRODUTO)) AS PRODUTO_ACABADO,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(FP.C2_FILIAL)),
                RTRIM(LTRIM(FP.C2_OP))
            ORDER BY FP.R_E_C_N_O_ DESC
        ) AS rn
    FROM SC2010 FP WITH (NOLOCK)
    WHERE FP.D_E_L_E_T_ = ''
      AND RIGHT(RTRIM(LTRIM(FP.C2_OP)), 5) = '{FINISHED_PRODUCTION_ORDER_SUFFIX}'
      {pa_branch_filter}
),
SHY_RANKED AS (
    SELECT
        RTRIM(LTRIM(SHY.HY_FILIAL)) AS match_filial,
        RTRIM(LTRIM(SHY.HY_OP)) AS match_op,
        RTRIM(LTRIM(SHY.HY_OPERAC)) AS match_operacao,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SHY.HY_TEMPOM)), ',', '.') AS FLOAT) AS HY_TEMPOM,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(SHY.HY_FILIAL)),
                RTRIM(LTRIM(SHY.HY_OP)),
                RTRIM(LTRIM(SHY.HY_OPERAC))
            ORDER BY SHY.R_E_C_N_O_ DESC
        ) AS rn
    FROM SHY010 SHY WITH (NOLOCK)
    WHERE SHY.D_E_L_E_T_ = ''
      {shy_branch_filter}
),
SG2_RANKED AS (
    SELECT
        RTRIM(LTRIM(SG2.G2_FILIAL)) AS match_filial,
        RTRIM(LTRIM(SG2.G2_PRODUTO)) AS match_produto,
        RTRIM(LTRIM(SG2.G2_OPERAC)) AS match_operacao,
        RTRIM(LTRIM(SG2.G2_DESCRI)) AS DESCRICAO_OPERACAO,
        TRY_CAST(REPLACE(LTRIM(RTRIM(SG2.G2_TEMPAD)), ',', '.') AS FLOAT) AS G2_TEMPAD,
        ROW_NUMBER() OVER (
            PARTITION BY
                RTRIM(LTRIM(SG2.G2_FILIAL)),
                RTRIM(LTRIM(SG2.G2_PRODUTO)),
                RTRIM(LTRIM(SG2.G2_OPERAC))
            ORDER BY SG2.R_E_C_N_O_ DESC
        ) AS rn
    FROM SG2010 SG2 WITH (NOLOCK)
    WHERE SG2.D_E_L_E_T_ = ''
      {sg2_branch_filter}
)"""
    return cte, tuple(params)


def build_ef_fabril_items_list_sql(
    *,
    where_clause: str,
    where_params: tuple,
    date_start: str,
    date_end: str,
    branch: str | None,
    branches: tuple[str, ...],
    offset: int | None = None,
    limit: int | None = None,
) -> tuple[str, tuple]:
    h6_cte, h6_params = build_fabril_sh6010_ranked_cte(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        branches=branches,
    )
    pa_sg2_cte, pa_sg2_params = build_fabril_pa_and_operation_ranked_ctes(
        branch=branch,
        branches=branches,
    )
    paging_sql = ""
    paging_params: tuple = ()
    if offset is not None and limit is not None:
        paging_sql = "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        paging_params = (offset, limit)

    sql = f"""
WITH
{h6_cte},
{pa_sg2_cte}
SELECT
    {EF_FABRIL_ITEMS_LIST_SELECT}
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{H6_RANKED_JOIN}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
{EF_FABRIL_PA_AND_OPERATION_JOINS}
WHERE {where_clause}
ORDER BY
    EF.DATA_PRODUCAO DESC,
    EF.HORA_INICIO DESC,
    EF.HORA_FINAL DESC
{paging_sql}
"""
    return sql, h6_params + pa_sg2_params + where_params + paging_params

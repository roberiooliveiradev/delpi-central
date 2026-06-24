"""Listagem eficiência fabril com appointment_id (mesmo vínculo SH6010 do OEE)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import EFICIENCIA_FABRIL_VIEW
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    FABRIL_SH6010_OUTER_APPLY,
)

EF_FABRIL_ITEMS_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{FABRIL_SH6010_OUTER_APPLY}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""

EF_FABRIL_ITEMS_SELECT = """
    H6.appointment_id AS appointment_id,
    RTRIM(LTRIM(EF.FILIAL)) AS FILIAL,
    RTRIM(LTRIM(EF.OP)) AS OP,
    RTRIM(LTRIM(EF.PRODUTO)) AS PRODUTO,
    RTRIM(LTRIM(EF.DESCRICAO_PRODUTO)) AS DESCRICAO_PRODUTO,
    RTRIM(LTRIM(SB1.B1_UM)) AS UNIDADE,
    RTRIM(LTRIM(EF.CENTRO_TRABALHO)) AS CENTRO_TRABALHO,
    RTRIM(LTRIM(EF.OPERACAO)) AS OPERACAO,
    RTRIM(LTRIM(EF.COD_OPERADOR)) AS COD_OPERADOR,
    RTRIM(LTRIM(EF.LOGIN_OPERADOR)) AS LOGIN_OPERADOR,
    RTRIM(LTRIM(EF.NOME_OPERADOR)) AS NOME_OPERADOR,
    EF.DATA_PRODUCAO AS DATA_PRODUCAO,
    RTRIM(LTRIM(EF.HORA_INICIO)) AS HORA_INICIO,
    RTRIM(LTRIM(EF.HORA_FINAL)) AS HORA_FINAL,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS QTD_APONTADA,
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

EF_FABRIL_ITEMS_LIST_SELECT = """
    H6.appointment_id AS appointment_id,
    EF.FILIAL AS FILIAL,
    EF.OP AS OP,
    EF.PRODUTO AS PRODUTO,
    EF.DESCRICAO_PRODUTO AS DESCRICAO_PRODUTO,
    RTRIM(LTRIM(SB1.B1_UM)) AS UNIDADE,
    EF.CENTRO_TRABALHO AS CENTRO_TRABALHO,
    EF.OPERACAO AS OPERACAO,
    EF.COD_OPERADOR AS COD_OPERADOR,
    EF.LOGIN_OPERADOR AS LOGIN_OPERADOR,
    EF.NOME_OPERADOR AS NOME_OPERADOR,
    EF.DATA_PRODUCAO AS DATA_PRODUCAO,
    EF.HORA_INICIO AS HORA_INICIO,
    EF.HORA_FINAL AS HORA_FINAL,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS QTD_APONTADA,
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


def build_fabril_sh6010_ranked_cte(
    *,
    date_start: str,
    date_end: str,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, tuple]:
    """Uma varredura em SH6010 por período (evita OUTER APPLY correlacionado em bulk)."""
    params: list = [date_start, date_end]
    if branch:
        branch_filter = "AND RTRIM(LTRIM(H6.H6_FILIAL)) = ?"
        params.append(branch)
    else:
        placeholders = ", ".join("?" for _ in branches)
        branch_filter = f"AND RTRIM(LTRIM(H6.H6_FILIAL)) IN ({placeholders})"
        params.extend(branches)

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
    paging_sql = ""
    paging_params: tuple = ()
    if offset is not None and limit is not None:
        paging_sql = "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        paging_params = (offset, limit)

    sql = f"""
WITH
{h6_cte}
SELECT
    {EF_FABRIL_ITEMS_LIST_SELECT}
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{H6_RANKED_JOIN}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
WHERE {where_clause}
ORDER BY
    EF.DATA_PRODUCAO DESC,
    EF.HORA_INICIO DESC,
    EF.HORA_FINAL DESC
{paging_sql}
"""
    return sql, h6_params + where_params + paging_params

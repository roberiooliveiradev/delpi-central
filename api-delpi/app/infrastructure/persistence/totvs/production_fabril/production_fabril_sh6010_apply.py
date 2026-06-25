"""Vínculo opcional view fabril → SH6010 (detalhe / appointment_id)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    DEFAULT_PRODUCTION_BRANCHES,
)

FABRIL_SH6010_OUTER_APPLY = """
OUTER APPLY (
    SELECT TOP 1
        CAST(H6.R_E_C_N_O_ AS BIGINT) AS appointment_id,
        RTRIM(LTRIM(H6.H6_RECURSO)) AS resource_code
    FROM SH6010 H6 WITH (NOLOCK)
    WHERE H6.D_E_L_E_T_ = ''
      AND RTRIM(LTRIM(H6.H6_FILIAL)) = RTRIM(LTRIM(EF.FILIAL))
      AND RTRIM(LTRIM(H6.H6_OP)) = RTRIM(LTRIM(EF.OP))
      AND CONVERT(DATE, H6.H6_DTPROD, 112) = EF.DATA_PRODUCAO
      AND RTRIM(LTRIM(ISNULL(H6.H6_HORAINI, ''))) = RTRIM(LTRIM(ISNULL(EF.HORA_INICIO, '')))
      AND RTRIM(LTRIM(ISNULL(H6.H6_HORAFIN, ''))) = RTRIM(LTRIM(ISNULL(EF.HORA_FINAL, '')))
      AND RTRIM(LTRIM(H6.H6_OPERAC)) = RTRIM(LTRIM(EF.OPERACAO))
    ORDER BY H6.R_E_C_N_O_ DESC
) H6
"""


def build_fabril_sh6010_scoped_left_join(
    *,
    date_start_protheus: str,
    date_end_protheus: str,
    branch: str | None = None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """
    Uma leitura de SH6010 no período/filial — join em lote em vez de APPLY por linha EF.
    """
    params: list = [date_start_protheus, date_end_protheus]
    if branch:
        branch_filter = "AND H6.H6_FILIAL = ?"
        params.append(branch)
    else:
        placeholders = ", ".join("?" for _ in branches)
        branch_filter = f"AND H6.H6_FILIAL IN ({placeholders})"
        params.extend(branches)

    sql = f"""
LEFT JOIN (
    SELECT
        appointment_id,
        resource_code,
        h6_branch,
        h6_op,
        h6_production_date,
        h6_start_time,
        h6_end_time,
        h6_operation
    FROM (
        SELECT
            CAST(H6.R_E_C_N_O_ AS BIGINT) AS appointment_id,
            RTRIM(LTRIM(H6.H6_RECURSO)) AS resource_code,
            RTRIM(LTRIM(H6.H6_FILIAL)) AS h6_branch,
            RTRIM(LTRIM(H6.H6_OP)) AS h6_op,
            CONVERT(DATE, H6.H6_DTPROD, 112) AS h6_production_date,
            RTRIM(LTRIM(ISNULL(H6.H6_HORAINI, ''))) AS h6_start_time,
            RTRIM(LTRIM(ISNULL(H6.H6_HORAFIN, ''))) AS h6_end_time,
            RTRIM(LTRIM(H6.H6_OPERAC)) AS h6_operation,
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
          AND H6.H6_DTPROD >= ?
          AND H6.H6_DTPROD <= ?
          {branch_filter}
    ) ranked
    WHERE ranked.rn = 1
) H6
    ON H6.h6_branch = RTRIM(LTRIM(EF.FILIAL))
   AND H6.h6_op = RTRIM(LTRIM(EF.OP))
   AND H6.h6_production_date = EF.DATA_PRODUCAO
   AND H6.h6_start_time = RTRIM(LTRIM(ISNULL(EF.HORA_INICIO, '')))
   AND H6.h6_end_time = RTRIM(LTRIM(ISNULL(EF.HORA_FINAL, '')))
   AND H6.h6_operation = RTRIM(LTRIM(EF.OPERACAO))
"""
    return sql, tuple(params)

"""Listagem OEE alinhada à view fabril (sem duplicar regras de eficiência fabril)."""

from app.domain.production.production_fabril_appointment_scope import (
    EFICIENCIA_FABRIL_VIEW,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    fabril_efficiency_status_expr,
)

OEE_FABRIL_APPOINTMENTS_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
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
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""

OEE_FABRIL_APPOINTMENTS_SELECT = f"""
SELECT
    H6.appointment_id AS appointment_id,
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    RTRIM(LTRIM(EF.OP)) AS production_order,
    RTRIM(LTRIM(EF.PRODUTO)) AS product_code,
    RTRIM(LTRIM(EF.DESCRICAO_PRODUTO)) AS product_description,
    RTRIM(LTRIM(SB1.B1_TIPO)) AS product_type,
    RTRIM(LTRIM(EF.CENTRO_TRABALHO)) AS work_center,
    RTRIM(LTRIM(EF.OPERACAO)) AS operation,
    H6.resource_code AS resource_code,
    RTRIM(LTRIM(EF.COD_OPERADOR)) AS operator_code,
    CONVERT(VARCHAR(10), EF.DATA_PRODUCAO, 23) AS production_date,
    RTRIM(LTRIM(EF.HORA_INICIO)) AS start_time,
    RTRIM(LTRIM(EF.HORA_FINAL)) AS end_time,
    ROUND(TRY_CAST(EF.EFICIENCIA_PERCENTUAL AS DECIMAL(18, 4)), 2) AS oee_pct,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS produced_qty,
    {fabril_efficiency_status_expr("EF.EFICIENCIA_PERCENTUAL")} AS status
{OEE_FABRIL_APPOINTMENTS_FROM}
"""

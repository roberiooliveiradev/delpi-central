"""Listagem OEE alinhada à view fabril (sem duplicar regras de eficiência fabril)."""

from app.domain.production.production_fabril_appointment_scope import (
    EFICIENCIA_FABRIL_VIEW,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    fabril_efficiency_status_expr,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    FABRIL_SH6010_OUTER_APPLY,
)

OEE_FABRIL_APPOINTMENTS_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{FABRIL_SH6010_OUTER_APPLY}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""


def build_oee_fabril_appointments_from(*, sh6010_join_sql: str) -> str:
    return f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{sh6010_join_sql}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""


def build_oee_fabril_appointments_select(*, sh6010_join_sql: str) -> str:
    return f"""
SELECT
    H6.appointment_id AS appointment_id,
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    RTRIM(LTRIM(EF.OP)) AS production_order,
    RTRIM(LTRIM(EF.PRODUTO)) AS product_code,
    RTRIM(LTRIM(EF.DESCRICAO_PRODUTO)) AS product_description,
    RTRIM(LTRIM(SB1.B1_UM)) AS unit,
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
{build_oee_fabril_appointments_from(sh6010_join_sql=sh6010_join_sql)}
"""


OEE_FABRIL_APPOINTMENTS_SELECT = f"""
SELECT
    H6.appointment_id AS appointment_id,
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    RTRIM(LTRIM(EF.OP)) AS production_order,
    RTRIM(LTRIM(EF.PRODUTO)) AS product_code,
    RTRIM(LTRIM(EF.DESCRICAO_PRODUTO)) AS product_description,
    RTRIM(LTRIM(SB1.B1_UM)) AS unit,
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

"""Listagem OEE alinhada à eficiência fabril (mesmo % canônico HY_TEMPAD × qtd)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    EFICIENCIA_FABRIL_VIEW,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    FABRIL_EFICIENCIA_PERCENTUAL_SQL,
    fabril_recalculated_efficiency_status_expr,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    FABRIL_SH6010_OUTER_APPLY,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_standard_time_sql import (
    FABRIL_STANDARD_TIME_JOINS,
)

OEE_FABRIL_APPOINTMENTS_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{FABRIL_SH6010_OUTER_APPLY}
{FABRIL_STANDARD_TIME_JOINS}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""


def build_oee_fabril_appointments_from(*, sh6010_join_sql: str) -> str:
    return f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{sh6010_join_sql}
{FABRIL_STANDARD_TIME_JOINS}
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.D_E_L_E_T_ = ''
   AND SB1.B1_COD = EF.PRODUTO
"""


def build_oee_fabril_appointments_select(*, sh6010_join_sql: str) -> str:
    status_expr = fabril_recalculated_efficiency_status_expr()
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
    ({FABRIL_EFICIENCIA_PERCENTUAL_SQL}) AS oee_pct,
    TRY_CAST(EF.QTD_APONTADA AS FLOAT) AS produced_qty,
    {status_expr} AS status
{build_oee_fabril_appointments_from(sh6010_join_sql=sh6010_join_sql)}
"""


OEE_FABRIL_APPOINTMENTS_SELECT = build_oee_fabril_appointments_select(
    sh6010_join_sql=FABRIL_SH6010_OUTER_APPLY,
)

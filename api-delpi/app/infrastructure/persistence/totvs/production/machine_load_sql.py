"""SQL builders — carga máquina (SH8010 + SC2010 + SB1010 + SG2010 + SHB010 + HZA010)."""

from __future__ import annotations

from app.domain.production.machine_load_scope import (
    DEFAULT_SORT,
    MACHINE_LOAD_ALLOCATION_TABLE,
    MACHINE_LOAD_ORDER_TABLE,
    MACHINE_LOAD_ORDERS_VIEW,
    MACHINE_LOAD_PRODUCT_TABLE,
    MACHINE_LOAD_ROUTING_TABLE,
    MACHINE_LOAD_WORK_CENTER_TABLE,
    SORT_DUE_DATE_ASC,
    SORT_DUE_DATE_DESC,
    SORT_ORDER_ASC,
    SORT_QTY_DESC,
    SORT_SCHEDULE_ASC,
    SORT_SCHEDULE_DESC,
    SORT_VALUES,
    VALID_MACHINE_LOAD_BRANCHES,
)
from app.domain.totvs.protheus_operation_appointments import (
    OPERATION_APPOINTMENT_TABLE,
    active_appointment_predicate_sql,
    active_marker_sql,
)
from app.domain.totvs.protheus_production_orders import mother_order_key_sql
from app.domain.totvs.protheus_users import operator_name_expr, operator_name_join_sql

_SCHEDULE_KEYS = "OA.H8_DTINI {0}, OA.H8_HRINI {0}, OA.H8_OP {0}, OA.H8_OPER {0}"

_IN_PRODUCTION_EXPR = "CASE WHEN ISNULL(AP.active_count, 0) > 0 THEN 1 ELSE 0 END"

# Entrega da própria OP (SC2, YYYYMMDD) — só entra quando a OP mãe não está na view PCP.
_ORDER_DUE_DATE_EXPR = "TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM(OP.C2_DATPRF)), ''), 112)"

# Entrega efetiva: a data da OP mãe manda; sem mãe, a previsão da própria OP evita
# operação sem data (o PCP planeja por entrega, então ninguém pode ficar sem ela).
DUE_DATE_EXPR = f"COALESCE(PA.DT_ENTREGA, {_ORDER_DUE_DATE_EXPR})"
DUE_DATE_SOURCE_EXPR = (
    "CASE WHEN PA.DT_ENTREGA IS NOT NULL THEN 'mother_order'"
    f" WHEN {_ORDER_DUE_DATE_EXPR} IS NOT NULL THEN 'order'"
    " ELSE '' END"
)

# Em produção primeiro: o operador olha a máquina para saber o que está rodando.
_PRODUCTION_FIRST = f"{_IN_PRODUCTION_EXPR} DESC"

SORT_SQL = {
    SORT_SCHEDULE_ASC: f"{_PRODUCTION_FIRST}, {_SCHEDULE_KEYS.format('ASC')}",
    SORT_SCHEDULE_DESC: f"{_PRODUCTION_FIRST}, {_SCHEDULE_KEYS.format('DESC')}",
    SORT_DUE_DATE_ASC: f"{DUE_DATE_EXPR} ASC, {_SCHEDULE_KEYS.format('ASC')}",
    SORT_DUE_DATE_DESC: f"{DUE_DATE_EXPR} DESC, {_SCHEDULE_KEYS.format('ASC')}",
    SORT_ORDER_ASC: "OA.H8_OP ASC, OA.H8_OPER ASC",
    SORT_QTY_DESC: (
        "CAST(OP.C2_QUANT AS DECIMAL(18, 6)) DESC, " + _SCHEDULE_KEYS.format("ASC")
    ),
}

def _appointment_join_sql() -> str:
    """Agregado da HZA por operação: ativo agora, operadores e histórico.

    O nível interno marca cada apontamento; o externo agrega. Assim cada data
    entra como um único parâmetro, na ordem: recência do ativo, depois histórico.

    O nome do operador é resolvido **dentro** do agregado, sobre a HZA já
    filtrada. Resolver SYS_USR no nível de fora custava mais de um minuto.
    """
    active_predicate = active_appointment_predicate_sql("Z")
    marker = active_marker_sql("Z", operator_name_expr=operator_name_expr("USR"))
    operator_join = operator_name_join_sql(
        alias="USR", operator_expr="LTRIM(RTRIM(Z.HZA_OPERAD))"
    )
    return f"""
        LEFT JOIN (
            SELECT
                A.ap_branch,
                A.ap_order,
                A.ap_operation,
                SUM(A.is_active) AS active_count,
                COUNT(DISTINCT CASE WHEN A.is_active = 1 THEN A.operator_code END)
                    AS active_operator_count,
                MAX(CASE WHEN A.is_active = 1 THEN A.active_marker ELSE '' END)
                    AS active_marker,
                MAX(A.active_marker) AS last_marker,
                COUNT(*) AS appointment_count,
                MAX(A.start_date) AS last_appointment_date
            FROM (
                SELECT
                    Z.HZA_FILIAL AS ap_branch,
                    Z.HZA_OP AS ap_order,
                    Z.HZA_OPERAC AS ap_operation,
                    Z.HZA_OPERAD AS operator_code,
                    Z.HZA_DTINI AS start_date,
                    {marker} AS active_marker,
                    CASE WHEN {active_predicate} THEN 1 ELSE 0 END AS is_active
                FROM {OPERATION_APPOINTMENT_TABLE} Z WITH (NOLOCK)
                {operator_join}
                WHERE Z.D_E_L_E_T_ = ''
                  AND Z.HZA_DTINI >= ?
            ) A
            GROUP BY A.ap_branch, A.ap_order, A.ap_operation
        ) AP
            ON AP.ap_branch = OA.H8_FILIAL
           AND AP.ap_order = OA.H8_OP
           AND AP.ap_operation = OA.H8_OPER
    """


def _from_clause() -> str:
    mother_key = mother_order_key_sql("OA.H8_OP")
    return f"""
        FROM {MACHINE_LOAD_ALLOCATION_TABLE} OA WITH (NOLOCK)
        INNER JOIN {MACHINE_LOAD_ORDER_TABLE} OP WITH (NOLOCK)
            ON OP.C2_FILIAL = OA.H8_FILIAL
           AND OP.C2_OP = OA.H8_OP
           AND OP.D_E_L_E_T_ = ''
        LEFT JOIN {MACHINE_LOAD_PRODUCT_TABLE} P WITH (NOLOCK)
            ON P.B1_COD = OP.C2_PRODUTO
           AND P.D_E_L_E_T_ = ''
        LEFT JOIN {MACHINE_LOAD_WORK_CENTER_TABLE} HB WITH (NOLOCK)
            ON HB.HB_FILIAL = OA.H8_FILIAL
           AND HB.HB_COD = OA.H8_CTRAB
           AND HB.D_E_L_E_T_ = ''
        LEFT JOIN {MACHINE_LOAD_ROUTING_TABLE} G2 WITH (NOLOCK)
            ON G2.G2_FILIAL = OA.H8_FILIAL
           AND G2.G2_PRODUTO = OP.C2_PRODUTO
           AND G2.G2_CODIGO = OP.C2_ROTEIRO
           AND G2.G2_OPERAC = OA.H8_OPER
           AND G2.D_E_L_E_T_ = ''
        LEFT JOIN {MACHINE_LOAD_ORDERS_VIEW} PA WITH (NOLOCK)
            ON PA.FILIAL = OA.H8_FILIAL
           AND PA.OP_CHAVE = {mother_key}
        {_appointment_join_sql()}
    """


def _branch_filter_sql(branch: str | None) -> tuple[str, list[str]]:
    if branch:
        return "OA.H8_FILIAL = ?", [branch]
    ordered = sorted(VALID_MACHINE_LOAD_BRANCHES)
    placeholders = ", ".join("?" for _ in ordered)
    return f"OA.H8_FILIAL IN ({placeholders})", list(ordered)


def build_join_params(
    *,
    appointment_active_since: str,
    appointment_history_since: str,
) -> tuple:
    """Parâmetros do FROM, na ordem em que os placeholders aparecem no SQL."""
    return (appointment_active_since, appointment_history_since)


def build_base_where(
    *,
    scheduled_start: str,
    scheduled_end: str,
    delivery_start: str | None = None,
    delivery_end: str | None = None,
    branch: str | None = None,
    work_center: str | None = None,
    product_code: str | None = None,
    production_order: str | None = None,
    tool: str | None = None,
    open_only: bool | None = True,
) -> tuple[str, tuple]:
    """Filtro comum. Programação em YYYYMMDD (nativo da H8_DTINI); entrega em ISO.

    Com ``delivery_start`` / ``delivery_end`` o recorte passa a ser a **entrega
    efetiva** do PA e a janela de programação é ignorada — é assim que o PCP
    enxerga a fila (o que vence primeiro, mesmo alocado para daqui a meses).

    O que está em produção agora entra mesmo fora do período: a programação
    costuma ficar para trás e a máquina precisa aparecer rodando.
    """
    branch_sql, branch_params = _branch_filter_sql(branch)
    params: list = []
    if delivery_start or delivery_end:
        period_parts = []
        if delivery_start:
            period_parts.append(f"{DUE_DATE_EXPR} >= ?")
            params.append(delivery_start)
        if delivery_end:
            period_parts.append(f"{DUE_DATE_EXPR} <= ?")
            params.append(delivery_end)
    else:
        period_parts = ["OA.H8_DTINI >= ?", "OA.H8_DTINI <= ?"]
        params.extend([scheduled_start, scheduled_end])

    clauses = [
        "OA.D_E_L_E_T_ = ''",
        f"(({' AND '.join(period_parts)}) OR {_IN_PRODUCTION_EXPR} = 1)",
        branch_sql,
    ]
    params.extend(branch_params)

    if work_center:
        clauses.append("LTRIM(RTRIM(OA.H8_CTRAB)) = ?")
        params.append(work_center.strip())
    if product_code:
        clauses.append("LTRIM(RTRIM(OP.C2_PRODUTO)) LIKE ?")
        params.append(f"%{product_code.strip()}%")
    if production_order:
        clauses.append("LTRIM(RTRIM(OA.H8_OP)) LIKE ?")
        params.append(f"%{production_order.strip()}%")
    if tool:
        clauses.append("LTRIM(RTRIM(OA.H8_FERRAM)) = ?")
        params.append(tool.strip())
    if open_only is True:
        clauses.append("OP.C2_QUANT > OP.C2_QUJE")
    elif open_only is False:
        clauses.append("OP.C2_QUANT <= OP.C2_QUJE")

    return " AND ".join(clauses), tuple(params)


def _split_filters(filters: dict) -> tuple[tuple, dict]:
    join_params = build_join_params(
        appointment_active_since=filters.pop("appointment_active_since"),
        appointment_history_since=filters.pop("appointment_history_since"),
    )
    return join_params, filters


def build_work_centers_query(**filters) -> tuple[str, tuple]:
    """Um registro por centro de trabalho — alimenta as abas da carga máquina."""
    join_params, filters = _split_filters(filters)
    where_sql, where_params = build_base_where(**filters)
    query = f"""
        SELECT
            LTRIM(RTRIM(OA.H8_CTRAB)) AS work_center,
            MAX(LTRIM(RTRIM(ISNULL(HB.HB_NOME, '')))) AS work_center_name,
            COUNT(*) AS operation_count,
            COUNT(DISTINCT LTRIM(RTRIM(OA.H8_OP))) AS order_count,
            SUM({_IN_PRODUCTION_EXPR}) AS in_production_count,
            MIN(OA.H8_DTINI) AS first_scheduled_date,
            MAX(OA.H8_DTINI) AS last_scheduled_date,
            MIN({DUE_DATE_EXPR}) AS first_due_date,
            MAX({DUE_DATE_EXPR}) AS last_due_date,
            SUM(CASE WHEN {DUE_DATE_EXPR} IS NULL THEN 1 ELSE 0 END) AS missing_due_date_count
        {_from_clause()}
        WHERE {where_sql}
          AND LTRIM(RTRIM(OA.H8_CTRAB)) <> ''
        GROUP BY LTRIM(RTRIM(OA.H8_CTRAB))
        ORDER BY LTRIM(RTRIM(OA.H8_CTRAB)) ASC
    """
    return query, (*join_params, *where_params)


def build_operations_count_query(**filters) -> tuple[str, tuple]:
    join_params, filters = _split_filters(filters)
    where_sql, where_params = build_base_where(**filters)
    query = f"""
        SELECT COUNT(*) AS total
        {_from_clause()}
        WHERE {where_sql}
    """
    return query, (*join_params, *where_params)


def build_operations_query(
    *,
    sort: str = DEFAULT_SORT,
    offset: int,
    page_size: int,
    **filters,
) -> tuple[str, tuple]:
    if sort not in SORT_VALUES:
        raise ValueError(f"sort inválido: {sort}")
    join_params, filters = _split_filters(filters)
    where_sql, where_params = build_base_where(**filters)
    query = f"""
        SELECT
            LTRIM(RTRIM(OA.H8_FILIAL)) AS branch,
            LTRIM(RTRIM(OA.H8_CTRAB)) AS work_center,
            LTRIM(RTRIM(ISNULL(HB.HB_NOME, ''))) AS work_center_name,
            OA.H8_DTINI AS scheduled_date,
            LTRIM(RTRIM(OA.H8_HRINI)) AS scheduled_start_time,
            OA.H8_DTFIM AS scheduled_end_date,
            LTRIM(RTRIM(OA.H8_HRFIM)) AS scheduled_end_time,
            LTRIM(RTRIM(OA.H8_OP)) AS production_order,
            LTRIM(RTRIM(OA.H8_OPER)) AS operation_code,
            LTRIM(RTRIM(ISNULL(G2.G2_DESCRI, ''))) AS operation_description,
            LTRIM(RTRIM(ISNULL(OA.H8_FERRAM, ''))) AS tool,
            LTRIM(RTRIM(ISNULL(OA.H8_RECURSO, ''))) AS resource,
            LTRIM(RTRIM(OP.C2_PRODUTO)) AS product_code,
            LTRIM(RTRIM(ISNULL(P.B1_DESC, ''))) AS product_description,
            LTRIM(RTRIM(ISNULL(OP.C2_UM, ''))) AS unit,
            CAST(OP.C2_QUANT AS DECIMAL(18, 6)) AS planned_qty,
            CAST(OP.C2_QUJE AS DECIMAL(18, 6)) AS produced_qty,
            CAST(OP.C2_QUANT - OP.C2_QUJE AS DECIMAL(18, 6)) AS pending_qty,
            PA.DT_ENTREGA AS pa_due_date,
            {DUE_DATE_EXPR} AS due_date,
            {DUE_DATE_SOURCE_EXPR} AS due_date_source,
            LTRIM(RTRIM(ISNULL(PA.OP_CHAVE, ''))) AS pa_production_order,
            LTRIM(RTRIM(ISNULL(PA.PRODUTO, ''))) AS pa_product_code,
            LTRIM(RTRIM(ISNULL(PA.DESC_PRODUTO, ''))) AS pa_product_description,
            ISNULL(AP.active_count, 0) AS active_appointment_count,
            ISNULL(AP.active_operator_count, 0) AS active_operator_count,
            ISNULL(AP.appointment_count, 0) AS appointment_count,
            ISNULL(AP.last_appointment_date, '') AS last_appointment_date,
            ISNULL(AP.active_marker, '') AS active_marker,
            ISNULL(AP.last_marker, '') AS last_marker
        {_from_clause()}
        WHERE {where_sql}
        ORDER BY {SORT_SQL[sort]}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    return query, (*join_params, *where_params, offset, page_size)


def build_appointment_status_query(
    *,
    branch: str,
    appointment_active_since: str,
    appointment_history_since: str,
) -> tuple[str, tuple]:
    """Status de apontamento por OP+operação — sem SH8 (enriquecimento vivo do snapshot)."""
    active_predicate = active_appointment_predicate_sql("Z")
    marker = active_marker_sql("Z", operator_name_expr=operator_name_expr("USR"))
    operator_join = operator_name_join_sql(
        alias="USR", operator_expr="LTRIM(RTRIM(Z.HZA_OPERAD))"
    )
    query = f"""
        SELECT
            LTRIM(RTRIM(A.ap_branch)) AS branch,
            LTRIM(RTRIM(A.ap_order)) AS production_order,
            LTRIM(RTRIM(A.ap_operation)) AS operation_code,
            SUM(A.is_active) AS active_appointment_count,
            COUNT(DISTINCT CASE WHEN A.is_active = 1 THEN A.operator_code END)
                AS active_operator_count,
            MAX(CASE WHEN A.is_active = 1 THEN A.active_marker ELSE '' END)
                AS active_marker,
            MAX(A.active_marker) AS last_marker,
            COUNT(*) AS appointment_count,
            MAX(A.start_date) AS last_appointment_date
        FROM (
            SELECT
                Z.HZA_FILIAL AS ap_branch,
                Z.HZA_OP AS ap_order,
                Z.HZA_OPERAC AS ap_operation,
                Z.HZA_OPERAD AS operator_code,
                Z.HZA_DTINI AS start_date,
                {marker} AS active_marker,
                CASE WHEN {active_predicate} THEN 1 ELSE 0 END AS is_active
            FROM {OPERATION_APPOINTMENT_TABLE} Z WITH (NOLOCK)
            {operator_join}
            WHERE Z.D_E_L_E_T_ = ''
              AND Z.HZA_FILIAL = ?
              AND Z.HZA_DTINI >= ?
        ) A
        GROUP BY A.ap_branch, A.ap_order, A.ap_operation
    """
    return query, (appointment_active_since, branch, appointment_history_since)

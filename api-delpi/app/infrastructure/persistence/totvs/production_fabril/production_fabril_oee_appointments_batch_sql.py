"""Batch OEE apontamentos — materializa view fabril uma vez (temp table)."""

OEE_APPOINTMENTS_TEMP_TABLE = "#Delpi_OeeAppointments"

OEE_APPOINTMENTS_MATERIALIZE_SQL = f"""
        SET NOCOUNT ON;
        DROP TABLE IF EXISTS {OEE_APPOINTMENTS_TEMP_TABLE};
        WITH
        {{leading_ctes}}
        APONTAMENTOS_OEE AS (
            {{appointments_select}}
            WHERE {{where_clause}}
        )
        SELECT *
        INTO {OEE_APPOINTMENTS_TEMP_TABLE}
        FROM APONTAMENTOS_OEE;
        CREATE CLUSTERED INDEX CX_Delpi_OeeAppointments
            ON {OEE_APPOINTMENTS_TEMP_TABLE} (production_date DESC, production_order, operation);
        SET NOCOUNT OFF;
"""

OEE_APPOINTMENTS_ALL_ROWS_FROM_TEMP = f"""
        SELECT *
        FROM {OEE_APPOINTMENTS_TEMP_TABLE};
"""

OEE_APPOINTMENTS_SUMMARY_FROM_TEMP = f"""
        SELECT
            COUNT(*) AS total_appointments,
            SUM(CASE WHEN status = 'valid' THEN 1 ELSE 0 END) AS valid_appointments,
            SUM(CASE WHEN status = 'outlier' THEN 1 ELSE 0 END) AS outlier_appointments,
            ROUND(AVG(CASE WHEN status = 'valid' THEN oee_pct END), 2) AS avg_oee_pct
        FROM {OEE_APPOINTMENTS_TEMP_TABLE}
        {{status_clause}}
"""

OEE_APPOINTMENTS_COUNT_FROM_TEMP = f"""
        SELECT COUNT(*) AS total
        FROM {OEE_APPOINTMENTS_TEMP_TABLE}
        {{status_clause}}
"""

OEE_APPOINTMENTS_PAGE_FROM_TEMP = f"""
        SELECT *
        FROM {OEE_APPOINTMENTS_TEMP_TABLE}
        {{status_clause}}
        {{order_clause}}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


def format_oee_appointments_materialize_sql(
    *,
    appointments_select: str,
    where_clause: str,
    leading_ctes: str = "",
) -> str:
    ctes = leading_ctes.strip()
    if ctes and not ctes.endswith(","):
        ctes = f"{ctes},"
    materialize = OEE_APPOINTMENTS_MATERIALIZE_SQL.format(
        leading_ctes=ctes,
        appointments_select=appointments_select,
        where_clause=where_clause,
    )
    return f"{materialize}\n{OEE_APPOINTMENTS_ALL_ROWS_FROM_TEMP}"


def format_oee_appointments_batch_sql(
    *,
    appointments_select: str,
    where_clause: str,
    status_clause: str,
    order_clause: str,
    leading_ctes: str = "",
) -> str:
    ctes = leading_ctes.strip()
    if ctes and not ctes.endswith(","):
        ctes = f"{ctes},"
    materialize = OEE_APPOINTMENTS_MATERIALIZE_SQL.format(
        leading_ctes=ctes,
        appointments_select=appointments_select,
        where_clause=where_clause,
    )
    summary = OEE_APPOINTMENTS_SUMMARY_FROM_TEMP.format(status_clause=status_clause)
    count = OEE_APPOINTMENTS_COUNT_FROM_TEMP.format(status_clause=status_clause)
    page = OEE_APPOINTMENTS_PAGE_FROM_TEMP.format(
        status_clause=status_clause,
        order_clause=order_clause,
    )
    return f"{materialize}\n{summary};\n{count};\n{page};"

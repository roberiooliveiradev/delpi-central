from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_appointments_batch_sql import (
    OEE_APPOINTMENTS_TEMP_TABLE,
    format_oee_appointments_batch_sql,
)


def test_oee_appointments_batch_sql_materializes_once() -> None:
    sql = format_oee_appointments_batch_sql(
        where_clause="EF.DATA_PRODUCAO >= ? AND EF.DATA_PRODUCAO <= ?",
        status_clause="",
        order_clause="ORDER BY production_date DESC",
    )

    assert sql.count("WITH APONTAMENTOS_OEE AS") == 1
    assert f"INTO {OEE_APPOINTMENTS_TEMP_TABLE}" in sql
    assert f"FROM {OEE_APPOINTMENTS_TEMP_TABLE}" in sql
    assert sql.count(f"FROM {OEE_APPOINTMENTS_TEMP_TABLE}") == 3
    assert "total_appointments" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql


def test_oee_appointments_batch_sql_applies_status_clause_on_temp() -> None:
    status_clause = "WHERE status = 'valid'"
    sql = format_oee_appointments_batch_sql(
        where_clause="1=1",
        status_clause=status_clause,
        order_clause="ORDER BY oee_pct DESC",
    )

    assert sql.count(status_clause) == 3


def test_oee_appointments_batch_sql_page_params_are_last() -> None:
    sql = format_oee_appointments_batch_sql(
        where_clause="EF.H6_FILIAL = ?",
        status_clause="",
        order_clause="ORDER BY appointment_id ASC",
    )

    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert sql.count("?") == 3

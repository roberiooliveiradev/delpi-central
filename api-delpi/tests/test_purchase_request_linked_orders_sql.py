from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_orders_sql import (
    build_recent_linked_orders_max_recno_sql,
    build_recent_linked_orders_sql,
    clamp_linked_orders_limit,
)


def test_recent_linked_orders_sql_joins_numsc_itemsc_and_binds_recno() -> None:
    sql = build_recent_linked_orders_sql(limit=50)
    assert "C7_NUMSC" in sql
    assert "C7_ITEMSC" in sql
    assert "C1_PEDIDO" not in sql
    assert "R_E_C_N_O_" in sql
    assert "SC7.R_E_C_N_O_ > ?" in sql
    assert "ORDER BY SC7.R_E_C_N_O_" in sql
    assert "C1_USER" in sql
    assert "C7_DATPRF" in sql


def test_recent_linked_orders_limit_is_clamped() -> None:
    sql = build_recent_linked_orders_sql(limit=9999)
    assert "SELECT TOP 500" in sql
    assert clamp_linked_orders_limit(0) == 1
    assert clamp_linked_orders_limit(100) == 100


def test_recent_linked_orders_max_recno_filters_linked_sc7() -> None:
    sql = build_recent_linked_orders_max_recno_sql()
    assert "MAX(SC7.R_E_C_N_O_)" in sql
    assert "C7_NUMSC" in sql
    assert "D_E_L_E_T_" in sql

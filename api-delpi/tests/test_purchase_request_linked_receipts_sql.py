from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_orders_sql import (
    clamp_linked_orders_limit,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_receipts_sql import (
    build_recent_linked_receipts_max_recno_sql,
    build_recent_linked_receipts_sql,
)


def test_recent_linked_receipts_sql_joins_itempc_and_sc() -> None:
    sql = build_recent_linked_receipts_sql(limit=50)
    assert "D1_ITEMPC" in sql
    assert "D1_PEDIDO" in sql
    assert "C7_NUMSC" in sql
    assert "C7_ITEMSC" in sql
    assert "C1_USER" in sql
    assert "C7_ITEM) = RTRIM(SD1.D1_ITEMPC)" in sql
    assert "SD1.R_E_C_N_O_ > ?" in sql
    assert "ORDER BY SD1.R_E_C_N_O_" in sql
    assert "D1_DTDIGIT" in sql


def test_recent_linked_receipts_limit_is_clamped() -> None:
    sql = build_recent_linked_receipts_sql(limit=9999)
    assert "SELECT TOP 500" in sql
    assert clamp_linked_orders_limit(0) == 1


def test_recent_linked_receipts_max_recno_filters_sd1_with_po() -> None:
    sql = build_recent_linked_receipts_max_recno_sql()
    assert "MAX(SD1.R_E_C_N_O_)" in sql
    assert "D1_PEDIDO" in sql
    assert "D_E_L_E_T_" in sql

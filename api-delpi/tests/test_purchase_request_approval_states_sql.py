from app.domain.totvs.protheus_purchase_request import (
    map_purchase_request_approval_status,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_states_sql import (
    build_purchase_request_approval_states_filters,
    build_purchase_request_approval_states_sql,
    clamp_approval_states_limit,
)


def test_approval_states_sql_selects_sc1_decision_fields() -> None:
    where, params = build_purchase_request_approval_states_filters(
        branches=["01"],
        date_from="2026-01-01",
        date_to="2026-01-31",
    )
    sql = build_purchase_request_approval_states_sql(where_clause=where, limit=100)
    assert "SC1010" in sql
    assert "C1_APROV" in sql
    assert "C1_NOMAPRO" in sql
    assert "C1_USER" in sql
    assert "C1_ITEM" in sql
    assert "D_E_L_E_T_" in sql
    assert "R_E_C_N_O_" not in sql
    assert params == ["01", "20260101", "20260131"]


def test_approval_states_filters_default_to_all_branches() -> None:
    where, params = build_purchase_request_approval_states_filters(
        branches=None,
        date_from="2026-01-01",
    )
    assert "IN (?, ?)" in where
    assert params[0] == "01"
    assert params[1] == "02"


def test_approval_states_limit_is_clamped() -> None:
    assert clamp_approval_states_limit(None) == 500
    assert clamp_approval_states_limit(99999) == 5000
    assert clamp_approval_states_limit(0) == 1
    sql = build_purchase_request_approval_states_sql(where_clause="1=1", limit=100)
    assert "SELECT TOP 101" in sql


def test_map_purchase_request_approval_status() -> None:
    assert map_purchase_request_approval_status("L") == "approved"
    assert map_purchase_request_approval_status("R") == "rejected"
    assert map_purchase_request_approval_status("B") == "blocked"
    assert map_purchase_request_approval_status("") == "unknown"
    assert map_purchase_request_approval_status(None) == "unknown"
    assert map_purchase_request_approval_status(" X ") == "unknown"

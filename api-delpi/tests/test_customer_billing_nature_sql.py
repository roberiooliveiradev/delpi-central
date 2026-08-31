"""Unit tests for portfolio billing nature SQL builders."""

from __future__ import annotations

import pytest

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    billing_12m_params,
    billing_series_params,
    build_customer_billing_12m_sql,
    build_customer_billing_series_sql,
    normalize_billing_nature,
)


def test_normalize_billing_nature_defaults_to_gross() -> None:
    assert normalize_billing_nature(None) == "gross"
    assert normalize_billing_nature("") == "gross"
    assert normalize_billing_nature("NET") == "net"


def test_normalize_billing_nature_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="nature"):
        normalize_billing_nature("open_order_value")


def test_gross_series_sql_uses_f2_valbrut() -> None:
    sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        nature="gross",
    )
    assert "F2_VALBRUT" in sql
    assert "VLR_VENDA" not in sql
    assert "D1_DTDIGIT" not in sql


def test_net_series_sql_uses_rol_amounts() -> None:
    sql = build_customer_billing_series_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        granularity="month",
        nature="net",
    )
    assert "F2_VALBRUT" not in sql
    assert "D2_VALICM" in sql
    assert "D1_DTDIGIT" in sql
    assert "FULL OUTER JOIN" in sql


def test_gross_12m_sql_preserves_note_base() -> None:
    sql = build_customer_billing_12m_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        nature="gross",
    )
    assert "note_base" in sql
    assert "F2_VALBRUT" in sql


def test_net_12m_sql_subtracts_returns() -> None:
    sql = build_customer_billing_12m_sql(
        where_pairs="(D2.D2_CLIENTE = ? AND D2.D2_LOJA = ?)",
        nature="net",
    )
    assert "devolucoes" in sql
    assert "D2_VALICM" in sql
    assert "F2_VALBRUT" not in sql


def test_billing_params_counts_match_placeholders() -> None:
    pairs = ["100", "01"]
    gross_params = billing_series_params(
        pair_params=pairs, start_date="20260101", end_date="20261231", nature="gross"
    )
    assert len(gross_params) == 4
    net_params = billing_series_params(
        pair_params=pairs, start_date="20260101", end_date="20261231", nature="net"
    )
    assert len(net_params) == 10

    g12 = billing_12m_params(
        pair_params=pairs,
        start_date="20260101",
        mid_date="20260701",
        end_date="20261231",
        nature="gross",
    )
    assert len(g12) == 6
    n12 = billing_12m_params(
        pair_params=pairs,
        start_date="20260101",
        mid_date="20260701",
        end_date="20261231",
        nature="net",
    )
    # mid×2 + pairs×2 + start/end×2 + exists start/end + mid×2 + pairs×2 + start/end
    assert len(n12) == 2 + 2 + 4 + 2 + 2 + 2

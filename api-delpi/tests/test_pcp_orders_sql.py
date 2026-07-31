"""Testes SQL — OPs PCP."""

from __future__ import annotations

import pytest

from app.domain.production.pcp_orders_view_scope import (
    PCP_ORDERS_VIEW,
    RANK_BY_VALUES,
)
from app.infrastructure.persistence.totvs.production import pcp_orders_sql as sql


def test_summary_query_uses_view_and_delivery_dates() -> None:
    query, params = sql.build_summary_query(
        delivery_start="2025-07-01",
        delivery_end="2026-07-01",
        branch="01",
    )
    assert PCP_ORDERS_VIEW in query
    assert "WITH (NOLOCK)" in query
    assert "DT_ENTREGA" in query
    assert params[:2] == ("2025-07-01", "2026-07-01")
    assert "01" in params


def test_summary_open_only_and_mother_filters() -> None:
    query, params = sql.build_summary_query(
        delivery_start="2025-07-01",
        delivery_end="2026-07-01",
        branch=None,
        open_only=True,
        mother_only=True,
        delayed_only=True,
    )
    assert "FL_OP_EM_ABERTO = 1" in query
    assert "FL_OP_MAE = 1" in query
    assert "FL_ATRASADA" in query
    assert "LTRIM(RTRIM(v.FILIAL)) IN (?, ?)" in query


def test_items_query_pagination() -> None:
    query, params = sql.build_items_query(
        delivery_start="2025-07-01",
        delivery_end="2026-07-01",
        branch="01",
        sort="delay_desc",
        offset=10,
        page_size=25,
    )
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params[-2:] == (10, 25)
    assert "saldo_op" in query


@pytest.mark.parametrize("rank_by", RANK_BY_VALUES)
def test_ranking_query_per_rank_by(rank_by: str) -> None:
    query, params = sql.build_ranking_query(
        delivery_start="2025-07-01",
        delivery_end="2026-07-01",
        branch="01",
        rank_by=rank_by,
        metric="order_qty",
        limit=10,
    )
    assert "SELECT TOP 10" in query
    assert "ORDER BY order_qty_sum DESC" in query
    assert params == ("2025-07-01", "2026-07-01", "01")

"""Testes SQL — horas improdutivas."""

from __future__ import annotations

import pytest

from app.domain.production.unproductive_hours_view_scope import (
    RANK_BY_VALUES,
    UNPRODUCTIVE_HOURS_VIEW,
)
from app.infrastructure.persistence.totvs.production import (
    unproductive_hours_sql as sql,
)


def test_summary_where_has_no_fixed_rt_motivo() -> None:
    query, params = sql.build_summary_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        branch="01",
    )
    assert UNPRODUCTIVE_HOURS_VIEW in query
    assert "WITH (NOLOCK)" in query
    assert "MOTIVO)) = ?" not in query.replace(" ", "")
    assert "RT" not in params
    assert params == ("2025-07-01", "2026-07-01", "01")


def test_summary_optional_stop_reason_filter() -> None:
    query, params = sql.build_summary_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        branch=None,
        stop_reason="OT",
    )
    assert "LTRIM(RTRIM(v.MOTIVO)) = ?" in query
    assert "LTRIM(RTRIM(v.FILIAL)) IN (?, ?)" in query
    assert params == ("2025-07-01", "2026-07-01", "01", "02", "OT")


def test_items_query_uses_descricao_motivo_from_view() -> None:
    query, params = sql.build_items_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        branch="01",
        sort="hours_desc",
        offset=0,
        page_size=50,
    )
    assert "DESCRICAO_MOTIVO" in query
    assert "motivo_descricao" in query
    assert "CYN010" not in query
    assert "CYN_DSSP" not in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params[-2:] == (0, 50)


@pytest.mark.parametrize("rank_by", RANK_BY_VALUES)
def test_ranking_query_group_by_per_rank_by(rank_by: str) -> None:
    query, params = sql.build_ranking_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        branch="01",
        rank_by=rank_by,
        metric="hours",
        limit=10,
    )
    assert f"SELECT TOP 10" in query
    assert "ORDER BY total_horas DESC" in query
    assert "GROUP BY" in query
    assert params == ("2025-07-01", "2026-07-01", "01")
    assert "CYN010" not in query
    if rank_by == "stop_reason":
        assert "DESCRICAO_MOTIVO" in query
        assert "motivo_descricao" in query


def test_ranking_metric_cost_orders_by_custo() -> None:
    query, _ = sql.build_ranking_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        branch="01",
        rank_by="resource",
        metric="cost",
        limit=5,
    )
    assert "ORDER BY total_custo DESC" in query
    assert "SELECT TOP 5" in query


def test_ranking_invalid_rank_by_raises() -> None:
    with pytest.raises(ValueError, match="rank_by"):
        sql.build_ranking_query(
            start_date="2025-07-01",
            end_date="2026-07-01",
            branch="01",
            rank_by="invalid",
            metric="hours",
            limit=10,
        )

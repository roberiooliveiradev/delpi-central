"""SQL contract for the settlements repository (read-only, parametrized)."""

from __future__ import annotations

import pytest

from app.infrastructure.persistence.totvs.financeiro_settlements import (
    settlements_sql,
)


def test_payables_list_query_binds_fk2_and_audited_joins() -> None:
    query, params = settlements_sql.build_settlements_list_query(
        side="payable",
        start_date="20260101",
        end_date="20260131",
        nature_code="100",
        movement_type="BA",
        sort_by="settlement_date",
        sort_dir="desc",
        page=2,
        page_size=50,
    )
    assert "FROM FK2010 F WITH (NOLOCK)" in query
    assert "F.D_E_L_E_T_ = ''" in query
    assert "T.FK7_ALIAS = 'SE2'" in query
    assert "LEFT JOIN SE2010" in query
    assert "LEFT JOIN SED010" in query
    assert "F.FK2_DATA >= ?" in query
    assert "F.FK2_NATURE = ?" in query
    assert "F.FK2_TPDOC = ?" in query
    assert "ORDER BY F.FK2_DATA DESC, F.FK2_IDFK2 DESC" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params == ("20260101", "20260131", "100", "BA", 50, 50)


def test_receivables_list_query_binds_fk1_and_title_composite() -> None:
    query, params = settlements_sql.build_settlements_list_query(
        side="receivable",
        start_date="20260101",
        end_date="20260131",
        sort_by="nature",
        sort_dir="asc",
        page=1,
        page_size=200,
    )
    assert "FROM FK1010 F WITH (NOLOCK)" in query
    assert "T.FK7_ALIAS = 'SE1'" in query
    assert "LEFT JOIN SE1010" in query
    assert "TITLE.E1_CLIENTE = T.FK7_CLIFOR" in query
    assert "TITLE.E1_FILIAL = T.FK7_FILTIT" in query
    assert "ORDER BY F.FK1_NATURE ASC, F.FK1_IDFK1 ASC" in query
    assert params == ("20260101", "20260131", 0, 200)


def test_count_query_never_joins() -> None:
    """Count on the fact table only — joins can never multiply the total."""
    query, _ = settlements_sql.build_settlements_count_query(
        side="payable", start_date="20260101", end_date="20260131"
    )
    assert "JOIN" not in query
    assert "COUNT(*) AS total_items" in query


def test_quality_query_counts_missing_links_without_dropping_rows() -> None:
    query, _ = settlements_sql.build_settlements_quality_query(
        side="receivable", start_date="20260101", end_date="20260131"
    )
    assert "missing_document" in query
    assert "missing_nature" in query
    assert "unresolved_branch" in query
    assert "LEFT JOIN FK7010" in query
    assert "LEFT JOIN SED010" in query


def test_summary_groups_by_side_currency_nature_movement() -> None:
    query, params = settlements_sql.build_settlements_summary_query(
        start_date="20260101",
        end_date="20260131",
        nature_code="100",
    )
    assert "UNION ALL" in query
    assert "'payable' AS side" in query
    assert "'receivable' AS side" in query
    assert "GROUP BY" in query
    assert "total_amount" in query
    # no merged/official total: per-dimension rows only
    assert params == ("20260101", "20260131", "100", "20260101", "20260131", "100")


def test_invalid_side_rejected() -> None:
    with pytest.raises(ValueError):
        settlements_sql.build_settlements_list_query(
            side="north",
            start_date="20260101",
            end_date="20260131",
            sort_by="settlement_date",
            sort_dir="asc",
            page=1,
            page_size=50,
        )


def test_sort_whitelist_rejects_unknown_column() -> None:
    with pytest.raises(KeyError):
        settlements_sql.build_settlements_list_query(
            side="payable",
            start_date="20260101",
            end_date="20260131",
            sort_by="injection",
            sort_dir="asc",
            page=1,
            page_size=50,
        )


def test_no_write_or_legacy_token_shapes() -> None:
    for builder in (
        settlements_sql.build_settlements_list_query,
        settlements_sql.build_settlements_count_query,
        settlements_sql.build_settlements_quality_query,
    ):
        query, _ = builder(
            side="payable",
            start_date="20260101",
            end_date="20260131",
            **({"sort_by": "settlement_date", "sort_dir": "asc", "page": 1, "page_size": 10}
               if builder is settlements_sql.build_settlements_list_query else {}),
        )
        for forbidden in ("INSERT", "UPDATE ", "DELETE ", "MERGE", "EXEC "):
            assert forbidden not in query.upper()

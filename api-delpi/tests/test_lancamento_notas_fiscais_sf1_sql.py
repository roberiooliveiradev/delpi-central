"""SQL de conciliação SF1 — match direto e beneficiamento (tipo B)."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_invoice_posting_sf1_sql import (
    build_find_active_by_fiscal_keys_sql,
)


def test_build_sql_empty_keys() -> None:
    sql, params = build_find_active_by_fiscal_keys_sql([])
    assert sql == ""
    assert params == []


def test_build_sql_skips_incomplete_keys() -> None:
    sql, params = build_find_active_by_fiscal_keys_sql(
        [{"branch_code": "01", "document_match_key": "004041160"}]
    )
    assert sql == ""
    assert params == []


def test_build_sql_includes_beneficiamento_bridge_and_projects_request_keys() -> None:
    sql, params = build_find_active_by_fiscal_keys_sql(
        [
            {
                "branch_code": "01",
                "supplier_code": "000123",
                "supplier_store": "01",
                "document_match_key": "004041160",
                "series": "1",
            },
            {
                # duplicata — deve colapsar
                "branch_code": "01",
                "supplier_code": "000123",
                "supplier_store": "01",
                "document_match_key": "004041160",
                "series": "1",
            },
        ]
    )
    assert "SF1010" in sql
    assert "F1_TIPO" in sql
    assert "SA1010" in sql
    assert "SA2010" in sql
    assert "A1_CGC" in sql
    assert "A2_CGC" in sql
    assert "VALUES" in sql
    assert "k.supplier_code AS supplier_code" in sql
    assert "erp_party_code" in sql
    assert params == [
        "01",
        "000123",
        "01",
        "004041160",
        "1",
    ]


def test_build_sql_normalizes_series_upper() -> None:
    _, params = build_find_active_by_fiscal_keys_sql(
        [
            {
                "branch_code": "02",
                "supplier_code": "1",
                "supplier_store": "01",
                "document_match_key": "000012078",
                "series": "u",
            }
        ]
    )
    assert params[-1] == "U"


def test_build_sql_canonicalizes_numeric_series_and_matches_sf1_without_padding() -> None:
    sql, params = build_find_active_by_fiscal_keys_sql(
        [
            {
                "branch_code": "02",
                "supplier_code": "000006",
                "supplier_store": "01",
                "document_match_key": "000186765",
                "series": "001",
            }
        ]
    )
    assert params[-1] == "1"
    assert "CONVERT(INT," in sql
    assert "F1_SERIE" in sql
    # 001 e 1 colapsam na mesma chave
    _, params_b = build_find_active_by_fiscal_keys_sql(
        [
            {
                "branch_code": "02",
                "supplier_code": "000006",
                "supplier_store": "01",
                "document_match_key": "000186765",
                "series": "1",
            },
            {
                "branch_code": "02",
                "supplier_code": "000006",
                "supplier_store": "01",
                "document_match_key": "000186765",
                "series": "001",
            },
        ]
    )
    assert params_b.count("1") == 1

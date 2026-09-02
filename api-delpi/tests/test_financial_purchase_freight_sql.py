from app.domain.totvs.protheus_freight_links import (
    FREIGHT_LINK_TYPE,
    FREIGHT_SERIES_COLUMNS,
    ORIGIN_SERIES_COLUMNS,
    series_coalesce_expr,
)
from app.infrastructure.persistence.totvs.financial_repositories.purchase_freight_sql import (
    build_purchase_freight_branch_filter,
    build_purchase_freight_links_params,
    build_purchase_freight_links_sql,
    build_purchase_freight_scope_filter,
)


def _sql() -> str:
    branch_clause, _ = build_purchase_freight_branch_filter("01")
    scope_clause, _ = build_purchase_freight_scope_filter(
        issue_start="2026-01-01",
        issue_end="2026-12-31",
        entry_start=None,
        entry_end=None,
        supplier=None,
        invoice_document=None,
        freight_document=None,
    )
    return build_purchase_freight_links_sql(
        branch_clause=branch_clause,
        scope_clause=scope_clause,
    )


def test_link_source_is_active_freight_tie_only() -> None:
    sql = _sql()

    assert "FROM SF8010 F8 WITH (NOLOCK)" in sql
    assert "F8.F8_TIPO = ?" in sql
    assert "F8.D_E_L_E_T_ = ''" in sql
    assert "SELECT DISTINCT" in sql


def test_both_invoice_and_freight_use_left_join_with_full_key() -> None:
    sql = _sql()

    assert "LEFT JOIN SF1010 NF WITH (NOLOCK)" in sql
    assert "LEFT JOIN SF1010 CTE WITH (NOLOCK)" in sql

    for alias, document, series, party, store in (
        ("NF", "invoice_document", "invoice_series", "supplier_code", "supplier_store"),
        ("CTE", "freight_document", "freight_series", "carrier_code", "carrier_store"),
    ):
        assert f"{alias}.F1_FILIAL = L.branch" in sql
        assert f"{alias}.F1_DOC = L.{document}" in sql
        assert f"{alias}.F1_SERIE = L.{series}" in sql
        assert f"{alias}.F1_FORNECE = L.{party}" in sql
        assert f"{alias}.F1_LOJA = L.{store}" in sql
        assert f"{alias}.D_E_L_E_T_ = ''" in sql


def test_monetary_columns_are_cast_to_decimal() -> None:
    sql = _sql()

    assert "CAST(NF.F1_VALMERC AS DECIMAL(18, 2))" in sql
    assert "CAST(CTE.F1_VALBRUT AS DECIMAL(18, 2))" in sql
    assert "FLOAT" not in sql.upper().replace("FLOAT_", "")


def test_series_mapping_covers_both_protheus_variants() -> None:
    sql = _sql()

    for column in (*FREIGHT_SERIES_COLUMNS, *ORIGIN_SERIES_COLUMNS):
        assert column in sql

    expression = series_coalesce_expr(FREIGHT_SERIES_COLUMNS, table_alias="F8")
    assert expression == "COALESCE(NULLIF(RTRIM(F8.F8_SEDIFRE), ''), NULLIF(RTRIM(F8.F8_SDOCFRE), ''), '')"


def test_date_filter_never_reaches_the_link_where_clause() -> None:
    """O filtro de data vira ``in_filter``; empurrá-lo quebraria a base de rateio."""
    sql = _sql()

    link_block = sql.split("PAIR AS (")[0]
    assert "F1_EMISSAO" not in link_block
    assert "F1_DTDIGIT" not in link_block
    assert "CASE WHEN" in sql.split("PAIR AS (")[1].split("FROM LINK L")[0]
    assert "AS in_filter" in sql


def test_selection_keeps_whole_freight_document_and_orphan_links() -> None:
    sql = _sql()

    assert "MATCHED AS (" in sql
    assert "WHERE in_filter = 1" in sql
    assert "AND invoice_found = 1" in sql
    assert "WHERE M.branch IS NOT NULL" in sql
    assert "OR P.in_filter = 1" in sql


def test_supplier_names_come_from_shared_sa2010() -> None:
    sql = _sql()

    assert "LEFT JOIN SA2010 SA2F WITH (NOLOCK)" in sql
    assert "LEFT JOIN SA2010 SA2T WITH (NOLOCK)" in sql
    assert "A2_FILIAL" not in sql


def test_scope_filter_is_parameterized() -> None:
    clause, params = build_purchase_freight_scope_filter(
        issue_start="2026-01-01",
        issue_end="2026-01-31",
        entry_start="2026-02-01",
        entry_end="2026-02-28",
        supplier="001992",
        invoice_document="000123456",
        freight_document="000000789",
    )

    assert clause.count("?") == len(params)
    assert params == (
        "20260101",
        "20260131",
        "20260201",
        "20260228",
        "001992",
        "000123456",
        "000000789",
    )
    assert "COALESCE(NF.F1_EMISSAO, L.link_entry_date) BETWEEN ? AND ?" in clause
    assert "COALESCE(NF.F1_DTDIGIT, L.link_entry_date) BETWEEN ? AND ?" in clause


def test_issue_and_entry_ranges_are_independent() -> None:
    only_issue, issue_params = build_purchase_freight_scope_filter(
        issue_start="2026-01-01",
        issue_end="2026-01-31",
        entry_start=None,
        entry_end=None,
        supplier=None,
        invoice_document=None,
        freight_document=None,
    )
    only_entry, entry_params = build_purchase_freight_scope_filter(
        issue_start=None,
        issue_end=None,
        entry_start="2026-01-01",
        entry_end="2026-01-31",
        supplier=None,
        invoice_document=None,
        freight_document=None,
    )

    assert "F1_EMISSAO" in only_issue and "F1_DTDIGIT" not in only_issue
    assert "F1_DTDIGIT" in only_entry and "F1_EMISSAO" not in only_entry
    assert issue_params == entry_params == ("20260101", "20260131")


def test_params_follow_the_query_text_order() -> None:
    params = build_purchase_freight_links_params(
        branch_params=("01",),
        scope_params=("20260101", "20261231"),
        fetch_limit=101,
    )

    assert params == (FREIGHT_LINK_TYPE, "01", "20260101", "20261231", 101)


def test_consolidated_branch_produces_no_predicate() -> None:
    clause, params = build_purchase_freight_branch_filter(None)

    assert clause == "1=1"
    assert params == ()

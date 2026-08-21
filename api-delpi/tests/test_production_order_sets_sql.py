"""SQL — conjuntos de ordens de produção incompletos."""

from __future__ import annotations

from app.domain.production.production_order_sets_scope import MAX_BOM_DEPTH
from app.infrastructure.persistence.totvs.production import (
    production_order_sets_sql as sql,
)


def test_summary_query_filters_by_branch_and_caps_recursion() -> None:
    query, params = sql.build_incomplete_sets_summary_query(branch="01")

    assert "C2_FILIAL = ?" in query
    assert "C2_QUANT > C2_QUJE" in query
    assert params == ("01", MAX_BOM_DEPTH)


def test_open_universe_excludes_orders_with_finish_date() -> None:
    """Encerrada (C2_DATRF) com saldo residual não puxa o conjunto para o detector."""
    query, _ = sql.build_incomplete_sets_summary_query(branch="01")

    assert "C2_DATRF IS NULL OR LTRIM(RTRIM(C2_DATRF)) = ''" in query
    assert "OP.C2_DATRF IS NULL OR LTRIM(RTRIM(OP.C2_DATRF)) = ''" in query


def test_consolidated_summary_spans_valid_branches() -> None:
    query, params = sql.build_incomplete_sets_summary_query(branch=None)

    assert "C2_FILIAL IN (?, ?)" in query
    assert params == ("01", "02", MAX_BOM_DEPTH)


def test_issued_from_is_applied_before_the_recursion_cap() -> None:
    """A emissão filtra o HAVING do #SET_ROOT, que vem antes da recursão."""
    _, params = sql.build_incomplete_sets_summary_query(
        branch="01", issued_from="20250101"
    )

    assert params == ("01", "20250101", MAX_BOM_DEPTH)


def test_page_query_appends_row_number_window_params() -> None:
    query, params = sql.build_incomplete_sets_query(
        offset=100, page_size=50, branch="02"
    )

    assert "ROW_NUMBER() OVER" in query
    assert "PG.set_rank > ? AND PG.set_rank <= ?" in query
    assert params == ("02", MAX_BOM_DEPTH, 100, 150)


def test_structure_validity_uses_the_mother_order_issue_date() -> None:
    """Estrutura vigente na emissão, não hoje.

    Comparar com a estrutura de hoje acusava conjunto criado corretamente antes
    de uma troca de engenharia (147 falsos positivos na filial 01).
    """
    query, _ = sql.build_incomplete_sets_summary_query(branch="01")

    assert "G1.G1_INI <= R.reference_date" in query
    assert "G1.G1_FIM >= R.reference_date" in query
    assert "C.G1_INI <= B.reference_date" in query
    assert "GETDATE()" not in query


def test_expected_components_exclude_raw_material_and_the_root_itself() -> None:
    query, _ = sql.build_incomplete_sets_summary_query(branch="01")

    assert "P.B1_TIPO IN ('PI', 'PA')" in query
    assert "'MP'" not in query
    assert "B.component_code <> SR.root_code" in query


def test_set_key_is_number_plus_item() -> None:
    """Um mesmo C2_NUM carrega até 96 itens, cada um com a própria OP mãe."""
    query, _ = sql.build_incomplete_sets_summary_query(branch="01")

    assert "GROUP BY OP.C2_FILIAL, OP.C2_NUM, OP.C2_ITEM" in query
    assert "A.set_item = E.set_item" in query


def test_sets_without_a_mother_order_are_skipped() -> None:
    query, _ = sql.build_incomplete_sets_summary_query(branch="01")

    assert "THEN OP.C2_PRODUTO END) IS NOT NULL" in query


def test_analytical_reads_use_nolock() -> None:
    query, _ = sql.build_incomplete_sets_query(offset=0, page_size=10, branch="01")

    assert query.count("WITH (NOLOCK)") >= 5


def test_page_orders_by_due_date_with_undated_sets_last() -> None:
    query, _ = sql.build_incomplete_sets_query(offset=0, page_size=10, branch="01")

    assert "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC" in query


def test_temp_tables_are_dropped_before_reuse() -> None:
    """A conexão volta ao pool; sem o drop a próxima chamada acha #SET_ROOT."""
    query, _ = sql.build_incomplete_sets_query(offset=0, page_size=10, branch="01")

    for table in ("#SET_ROOT", "#BOM", "#DIFF", "#PER_SET"):
        assert f"DROP TABLE IF EXISTS {table};" in query

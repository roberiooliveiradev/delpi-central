from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    MAX_FORNECEDORES_FILTROS,
    build_centros_custo_query,
    build_filiais_query,
    build_fornecedores_query,
    build_period_where,
)


def test_build_period_where_requires_date_range() -> None:
    where_clause, params = build_period_where(
        start_date="20250601",
        end_date="20250630",
    )

    assert where_clause == "data_emissao BETWEEN ? AND ?"
    assert params == ("20250601", "20250630")


def test_build_period_where_applies_branch_filter() -> None:
    where_clause, params = build_period_where(
        start_date="20250601",
        end_date="20250630",
        branch="01",
    )

    assert "LTRIM(RTRIM(filial)) = ?" in where_clause
    assert params == ("20250601", "20250630", "01")


def test_build_filiais_query_uses_view_without_select_star() -> None:
    query, params = build_filiais_query(
        start_date="20250601",
        end_date="20250630",
        branch="02",
    )

    assert "dbo.vw_fin_despesas_centro_custo WITH (NOLOCK)" in query
    assert "SELECT DISTINCT" in query
    assert "SELECT *" not in query
    assert "ORDER BY codigo" in query
    assert params == ("20250601", "20250630", "02")


def test_build_centros_custo_query_selects_explicit_columns() -> None:
    query, _params = build_centros_custo_query(
        start_date="20250101",
        end_date="20251231",
    )

    assert "centro_custo_codigo" in query
    assert "centro_custo_descricao" in query
    assert "SELECT *" not in query


def test_build_fornecedores_query_limits_distinct_rows() -> None:
    query, _params = build_fornecedores_query(
        start_date="20250101",
        end_date="20251231",
    )

    assert f"TOP ({MAX_FORNECEDORES_FILTROS})" in query
    assert "fornecedor_cliente_codigo" in query
    assert "razao_social" in query


def test_build_fornecedores_query_applies_cost_center_filter() -> None:
    query, params = build_fornecedores_query(
        start_date="20250101",
        end_date="20251231",
        cost_center="0205",
    )

    assert "LTRIM(RTRIM(centro_custo_codigo)) = ?" in query
    assert "0205" in params

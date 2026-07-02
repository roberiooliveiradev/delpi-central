from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
    DespesasCentroCustoQueryRequest,
)
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    build_query_where,
    build_ranking_centros_query,
    build_ranking_fornecedores_query,
    build_resumo_query,
    build_serie_query,
)


def test_build_query_where_applies_optional_filters() -> None:
    where_clause, params = build_query_where(
        start_date="20250601",
        end_date="20250630",
        branch="01",
        cost_center="0101",
        supplier_code="003287",
        supplier_store="01",
    )

    assert "data_emissao BETWEEN ? AND ?" in where_clause
    assert "LTRIM(RTRIM(filial)) = ?" in where_clause
    assert "LTRIM(RTRIM(centro_custo_codigo)) = ?" in where_clause
    assert "LTRIM(RTRIM(fornecedor_cliente_codigo)) = ?" in where_clause
    assert "LTRIM(RTRIM(loja)) = ?" in where_clause
    assert params == ("20250601", "20250630", "01", "0101", "003287", "01")


def test_build_resumo_query_uses_aggregation_without_select_star() -> None:
    query, params = build_resumo_query(
        start_date="20250601",
        end_date="20250630",
        branch="01",
    )

    assert "data_emissao BETWEEN ? AND ?" in query
    assert "SUM(CAST(valor_total AS DECIMAL(18, 2)))" in query
    assert "MAX(CAST(valor_total AS DECIMAL(18, 2)))" in query
    assert "SELECT *" not in query
    assert params == ("20250601", "20250630", "01")


def test_build_serie_query_groups_by_month() -> None:
    query, params = build_serie_query(
        start_date="20250601",
        end_date="20260630",
        cost_center="0101",
    )

    assert "LEFT(LTRIM(RTRIM(data_emissao)), 6)" in query
    assert "GROUP BY LEFT(LTRIM(RTRIM(data_emissao)), 6)" in query
    assert "ORDER BY ano_mes ASC" in query
    assert "SELECT *" not in query
    assert params == ("20250601", "20260630", "0101")


def test_build_ranking_centros_query_uses_default_limit() -> None:
    query, params = build_ranking_centros_query(
        start_date="20250601",
        end_date="20250630",
        supplier_code="003287",
        supplier_store="01",
    )

    assert f"TOP ({DEFAULT_RANKING_LIMIT})" in query
    assert "percentual" in query
    assert "SELECT *" not in query
    assert params == ("20250601", "20250630", "003287", "01")


def test_build_ranking_centros_query_caps_limit_at_maximum() -> None:
    query, _params = build_ranking_centros_query(
        start_date="20250601",
        end_date="20250630",
        limit=999,
    )

    assert f"TOP ({MAX_RANKING_LIMIT})" in query


def test_build_ranking_fornecedores_query_applies_cost_center_filter() -> None:
    query, params = build_ranking_fornecedores_query(
        start_date="20250601",
        end_date="20250630",
        branch="02",
        cost_center="0101",
        limit=25,
    )

    assert "LTRIM(RTRIM(centro_custo_codigo)) = ?" in query
    assert "TOP (25)" in query
    assert params == ("20250601", "20250630", "02", "0101")


def test_query_request_resolve_ranking_limit_defaults_and_caps() -> None:
    default_request = DespesasCentroCustoQueryRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
    )
    capped_request = DespesasCentroCustoQueryRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
        limit=999,
    )

    assert default_request.resolve_ranking_limit() == DEFAULT_RANKING_LIMIT
    assert capped_request.resolve_ranking_limit() == MAX_RANKING_LIMIT

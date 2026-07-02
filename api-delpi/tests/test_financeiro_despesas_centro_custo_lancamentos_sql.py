from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_request import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DespesasCentroCustoLancamentosRequest,
)
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    SEARCH_FIELDS,
    build_lancamentos_count_query,
    build_lancamentos_data_query,
    build_lancamentos_where,
    resolve_lancamentos_order_by,
)


def test_build_lancamentos_where_applies_search_with_parameters() -> None:
    where_clause, params = build_lancamentos_where(
        start_date="20250601",
        end_date="20250630",
        branch="01",
        cost_center="0101",
        supplier_code="003287",
        supplier_store="01",
        search="cafe",
    )

    assert "data_emissao BETWEEN ? AND ?" in where_clause
    assert "LTRIM(RTRIM(filial)) = ?" in where_clause
    assert "LTRIM(RTRIM(centro_custo_codigo)) = ?" in where_clause
    assert "LTRIM(RTRIM(fornecedor_cliente_codigo)) = ?" in where_clause
    assert "LTRIM(RTRIM(loja)) = ?" in where_clause
    assert " COLLATE Latin1_General_CI_AI LIKE ?" in where_clause
    assert "%cafe%" not in where_clause
    assert params[:4] == ("20250601", "20250630", "01", "0101")
    assert params[4:6] == ("003287", "01")
    assert params[6:] == tuple(["%cafe%"] * len(SEARCH_FIELDS))


def test_build_lancamentos_count_query_without_select_star() -> None:
    query, params = build_lancamentos_count_query(
        start_date="20250601",
        end_date="20250630",
    )

    assert "SELECT COUNT(*) AS total_items" in query
    assert "data_emissao BETWEEN ? AND ?" in query
    assert "SELECT *" not in query
    assert params == ("20250601", "20250630")


def test_build_lancamentos_data_query_uses_offset_fetch_and_explicit_columns() -> None:
    query, params = build_lancamentos_data_query(
        start_date="20250601",
        end_date="20250630",
        sort_by="valor_total",
        sort_dir="desc",
        page=2,
        page_size=50,
    )

    assert "data_emissao BETWEEN ? AND ?" in query
    assert "CAST(valor_total AS DECIMAL(18, 2)) DESC" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert "SELECT *" not in query
    assert "recno_sd1" in query
    assert params == ("20250601", "20250630", 50, 50)


def test_resolve_lancamentos_order_by_rejects_unknown_field() -> None:
    try:
        resolve_lancamentos_order_by(sort_by="invalid", sort_dir="asc")
    except ValueError as exc:
        assert "sort_by inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown sort_by")


def test_lancamentos_request_defaults_and_page_size_cap() -> None:
    request = DespesasCentroCustoLancamentosRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
    )

    assert request.resolve_page() == 1
    assert request.resolve_page_size() == DEFAULT_PAGE_SIZE

    capped = DespesasCentroCustoLancamentosRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
        page_size=999,
    )
    assert capped.resolve_page_size() == MAX_PAGE_SIZE


def test_lancamentos_request_rejects_invalid_sort_by_and_sort_dir() -> None:
    try:
        DespesasCentroCustoLancamentosRequest.from_query(
            start_date="2025-06-01",
            end_date="2025-06-30",
            sort_by="drop_table",
        )
    except ValueError as exc:
        assert "sort_by inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid sort_by")

    try:
        DespesasCentroCustoLancamentosRequest.from_query(
            start_date="2025-06-01",
            end_date="2025-06-30",
            sort_dir="sideways",
        )
    except ValueError as exc:
        assert "sort_dir inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid sort_dir")

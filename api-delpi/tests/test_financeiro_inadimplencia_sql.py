from app.application.dto.financeiro_inadimplencia.clientes_request import (
    InadimplenciaClientesRequest,
)
from app.application.dto.financeiro_inadimplencia.constantes import MAX_PAGE_SIZE
from app.application.dto.financeiro_inadimplencia.titulos_request import (
    InadimplenciaTitulosRequest,
)
from app.infrastructure.persistence.totvs.financeiro_inadimplencia.inadimplencia_sql import (
    CLIENTES_SEARCH_FIELDS,
    TITULOS_SEARCH_FIELDS,
    build_clientes_count_query,
    build_clientes_data_query,
    build_faixas_atraso_query,
    build_mensal_query,
    build_period_where,
    build_resumo_query,
    build_titulos_count_query,
    build_titulos_data_query,
    build_titulos_where,
    resolve_clientes_order_by,
    resolve_titulos_order_by,
)


def test_build_period_where_uses_exclusive_end() -> None:
    where_clause, params = build_period_where(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
    )
    assert "MES_REFERENCIA >= ? AND MES_REFERENCIA < ?" in where_clause
    assert "LTRIM(RTRIM(CLIENTE)) NOT IN (?)" in where_clause
    assert params == ("2025-07-01", "2026-07-01", "000207")


def test_build_resumo_query_aggregates_without_select_star() -> None:
    query, params = build_resumo_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
    )
    assert "SUM(PAGO_EM_DIA)" in query
    assert "SUM(PAGO_COM_ATRASO)" in query
    assert "VW_FINANCEIRO_INADIMPLENCIA" in query
    assert "SELECT *" not in query
    assert "LTRIM(RTRIM(CLIENTE)) NOT IN (?)" in query
    assert params == ("2025-07-01", "2026-07-01", "000207")


def test_build_mensal_query_groups_by_mes_referencia() -> None:
    query, params = build_mensal_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
    )
    assert "GROUP BY MES_REFERENCIA" in query
    assert "ORDER BY MES_REFERENCIA ASC" in query
    assert params == ("2025-07-01", "2026-07-01", "000207")


def test_build_mensal_query_filters_customer_and_store() -> None:
    query, params = build_mensal_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        customer_code="000001",
        store_code="09",
    )
    assert "LTRIM(RTRIM(CLIENTE)) = ?" in query
    assert "LTRIM(RTRIM(LOJA)) = ?" in query
    assert params == ("2025-07-01", "2026-07-01", "000207", "000001", "09")


def test_build_mensal_query_filters_customer_pairs() -> None:
    query, params = build_mensal_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        customer_pairs=(("000001", "09"), ("000179", "01")),
    )
    assert query.count("LTRIM(RTRIM(CLIENTE)) = ? AND LTRIM(RTRIM(LOJA)) = ?") == 2
    assert " OR " in query
    assert params == (
        "2025-07-01",
        "2026-07-01",
        "000207",
        "000001",
        "09",
        "000179",
        "01",
    )


def test_build_mensal_query_novos_negocios_excludes_weg() -> None:
    query, params = build_mensal_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        novos_negocios=True,
    )
    assert "LTRIM(RTRIM(CLIENTE)) <> ?" in query
    assert params == ("2025-07-01", "2026-07-01", "000207", "000001")


def test_build_faixas_query() -> None:
    query, params = build_faixas_atraso_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
    )
    assert "GROUP BY LTRIM(RTRIM(FAIXA_ATRASO))" in query
    assert params == ("2025-07-01", "2026-07-01", "000207")


def test_build_clientes_queries_apply_search_and_pagination() -> None:
    count_query, count_params = build_clientes_count_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        q="WEG",
        only_with_delays=True,
    )
    assert "HAVING COALESCE(SUM(PAGO_COM_ATRASO), 0) > 0" in count_query
    assert count_params[0:3] == ("2025-07-01", "2026-07-01", "000207")
    assert count_params[3:] == tuple(["%WEG%"] * len(CLIENTES_SEARCH_FIELDS))

    data_query, data_params = build_clientes_data_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        q=None,
        only_with_delays=False,
        sort_by="late_amount",
        sort_dir="desc",
        page=2,
        page_size=20,
    )
    assert "HAVING" not in data_query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in data_query
    assert data_params[-2:] == (20, 20)


def test_build_titulos_where_applies_customer_status_faixa_and_search() -> None:
    where_clause, params = build_titulos_where(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        customer_code="000001",
        store_code="09",
        status="late",
        delay_range="ATRASO_ACIMA_30_DIAS",
        q="014413",
    )
    assert "LTRIM(RTRIM(CLIENTE)) = ?" in where_clause
    assert "LTRIM(RTRIM(LOJA)) = ?" in where_clause
    assert "PAGO_COM_ATRASO = 1" in where_clause
    assert "LTRIM(RTRIM(FAIXA_ATRASO)) = ?" in where_clause
    assert params[:6] == (
        "2025-07-01",
        "2026-07-01",
        "000207",
        "000001",
        "09",
        "ATRASO_ACIMA_30_DIAS",
    )
    assert params[6:] == tuple(["%014413%"] * len(TITULOS_SEARCH_FIELDS))


def test_build_titulos_data_query_uses_offset_and_whitelist_order() -> None:
    query, params = build_titulos_data_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        sort_by="amount",
        sort_dir="desc",
        page=1,
        page_size=20,
    )
    assert "CAST(VALOR_TITULO AS DECIMAL(18, 2)) DESC" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert "SELECT *" not in query
    assert params[-2:] == (0, 20)


def test_resolve_order_by_rejects_unknown_sort() -> None:
    try:
        resolve_clientes_order_by(sort_by="drop_table", sort_dir="asc")
    except ValueError as exc:
        assert "sort_by inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for clientes sort_by")

    try:
        resolve_titulos_order_by(sort_by="hack", sort_dir="desc")
    except ValueError as exc:
        assert "sort_by inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for titulos sort_by")


def test_resolve_titulos_order_by_avoids_duplicate_payment_date() -> None:
    order_by = resolve_titulos_order_by(sort_by="payment_date", sort_dir="desc")
    assert order_by.count("DATA_BAIXA") == 1
    assert order_by.startswith("DATA_BAIXA DESC")

    order_by_days = resolve_titulos_order_by(sort_by="days_late", sort_dir="desc")
    assert order_by_days.count("DIAS_ATRASO") == 1
    assert order_by_days.startswith("DIAS_ATRASO DESC")


def test_resolve_clientes_order_by_avoids_duplicate_customer_name() -> None:
    order_by = resolve_clientes_order_by(sort_by="customer_name", sort_dir="asc")
    assert order_by.count("nome_cliente") == 1
    assert order_by.startswith("nome_cliente ASC")


def test_request_page_size_cap_and_sort_whitelist() -> None:
    clientes = InadimplenciaClientesRequest.from_query(
        start_date="2025-07-01",
        end_date="2026-07-01",
        page_size=999,
    )
    assert clientes.resolve_page_size() == MAX_PAGE_SIZE

    try:
        InadimplenciaClientesRequest.from_query(
            start_date="2025-07-01",
            end_date="2026-07-01",
            sort_by="invalid",
        )
    except ValueError as exc:
        assert "sort_by inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for clientes sort whitelist")

    try:
        InadimplenciaTitulosRequest.from_query(
            start_date="2025-07-01",
            end_date="2026-07-01",
            status="maybe",
        )
    except ValueError as exc:
        assert "status inválido" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid status")


def test_titulos_count_query() -> None:
    query, params = build_titulos_count_query(
        start_date="2025-07-01",
        end_date_exclusive="2026-07-01",
        status="on_time",
    )
    assert "SELECT COUNT(*) AS total_items" in query
    assert "PAGO_EM_DIA = 1" in query
    assert params == ("2025-07-01", "2026-07-01", "000207")

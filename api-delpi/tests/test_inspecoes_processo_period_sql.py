from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_period_sql import (
    build_por_ensaiador_period_sql,
    build_por_produto_period_sql,
    build_resumo_period_sql,
    build_period_filter_clause,
)


def test_period_filter_clause_is_sargable() -> None:
    where_sql, params = build_period_filter_clause(
        "02",
        start_date="2026-08-01",
        end_date="2026-08-14",
    )
    assert "Data_Medicao_Date >= ?" in where_sql
    assert "Data_Medicao_Date <= ?" in where_sql
    assert "UPPER(" not in where_sql
    assert params == ["02", "2026-08-01", "2026-08-14"]


def test_resumo_period_sql_uses_historico_tela_and_nolock() -> None:
    sql, params = build_resumo_period_sql(
        "02",
        start_date="2026-08-01",
        end_date="2026-08-14",
    )
    assert "vw_minha_delpi_inspecoes_processo_historico_tela" in sql
    assert "WITH (NOLOCK)" in sql
    assert "Data_Medicao_Date >= ?" in sql
    assert "COUNT(DISTINCT" not in sql
    assert "resumo_filial" not in sql
    assert params == ["02", "2026-08-01", "2026-08-14"]


def test_por_produto_period_sql_limits_and_groups_by_product() -> None:
    sql, params = build_por_produto_period_sql(
        "01",
        start_date="2026-08-01",
        end_date="2026-08-14",
        limit=10,
    )
    assert "GROUP BY Filial, Codigo_Produto" in sql
    assert "OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert "COUNT(DISTINCT" not in sql
    assert params == ["01", "2026-08-01", "2026-08-14", 10]


def test_por_ensaiador_period_sql_groups_by_matricula() -> None:
    sql, params = build_por_ensaiador_period_sql(
        "01",
        start_date="2026-08-01",
        end_date=None,
        limit=10,
    )
    assert "GROUP BY Filial, Matricula_Ensaiador" in sql
    assert "Data_Medicao_Date <= ?" not in sql
    assert params == ["01", "2026-08-01", 10]

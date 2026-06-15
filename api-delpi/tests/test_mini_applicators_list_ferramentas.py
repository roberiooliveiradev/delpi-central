from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_query_parts import (
    codigo_filter_sql,
    codigo_prefix_pattern,
)


def test_codigo_prefix_pattern():
    assert codigo_prefix_pattern("23") == "23%"
    assert codigo_prefix_pattern(" 23-026 ") == "23-026%"


def test_codigo_filter_sql_busca_pelo_inicio():
    clause = codigo_filter_sql()
    assert "RTRIM(LTRIM(SB1.B1_COD)) LIKE ?" in clause
    assert "B1_GRUPO" in clause
    assert "B1_COD)) LIKE ?" in clause

from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_query_parts import (
    bloqueado_filter_sql,
    codigo_filter_sql,
    codigo_prefix_pattern,
    is_protheus_product_blocked,
)


def test_codigo_prefix_pattern():
    assert codigo_prefix_pattern("23") == "23%"
    assert codigo_prefix_pattern(" 23-026 ") == "23-026%"


def test_codigo_filter_sql_busca_pelo_inicio():
    clause = codigo_filter_sql()
    assert "RTRIM(LTRIM(SB1.B1_COD)) LIKE ?" in clause
    assert "B1_GRUPO" in clause
    assert "B1_COD)) LIKE ?" in clause


def test_bloqueado_filter_sql_exclui_produtos_bloqueados():
    clause = bloqueado_filter_sql()
    assert "B1_MSBLQL" in clause
    assert "'1'" in clause
    assert "'SIM'" in clause


def test_is_protheus_product_blocked():
    assert is_protheus_product_blocked("1") is True
    assert is_protheus_product_blocked("SIM") is True
    assert is_protheus_product_blocked("2") is False
    assert is_protheus_product_blocked("NAO") is False
    assert is_protheus_product_blocked(None) is False
    assert is_protheus_product_blocked("") is False

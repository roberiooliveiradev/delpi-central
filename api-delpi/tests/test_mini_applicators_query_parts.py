from app.infrastructure.persistence.totvs.engineering_repositories.mini_applicators_query_parts import (
    append_descricao_terms,
    bom_validity_where_clauses,
    peca_codigo_filter_sql,
)


def test_peca_codigo_filter_sql():
    assert peca_codigo_filter_sql(alias="C") == "RTRIM(LTRIM(C.B1_COD)) LIKE ?"


def test_append_descricao_terms_adiciona_or_entre_palavras():
    where: list[str] = []
    params: list = []
    append_descricao_terms(
        column_sql="C.B1_DESC",
        descricao="grampeador isolante",
        where_clauses=where,
        params=params,
    )
    assert len(where) == 1
    assert "OR" in where[0]
    assert len(params) == 2


def test_bom_validity_where_clauses_usa_alias():
    clauses = bom_validity_where_clauses(alias="G")
    assert len(clauses) == 2
    assert all("G.G1_" in clause for clause in clauses)

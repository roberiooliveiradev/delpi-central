from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    _build_historico_where,
)


def test_build_historico_where_uses_sargable_product_and_op_filters() -> None:
    where_clause, params = _build_historico_where(
        "01",
        ordem_producao=" 10565201002 ",
        codigo_produto="90263652",
        resultado="a",
    )

    assert "UPPER(" not in where_clause
    assert "LTRIM(" not in where_clause
    assert "RTRIM(" not in where_clause
    assert "Ordem_Producao LIKE ?" in where_clause
    assert "Codigo_Produto LIKE ?" in where_clause
    assert "Resultado_Inspecao_Codigo = ?" in where_clause
    assert params == ["01", "10565201002%", "90263652%", "A"]


def test_build_historico_where_ignores_blank_optional_filters() -> None:
    where_clause, params = _build_historico_where(
        "02",
        ordem_producao="   ",
        codigo_produto="",
        resultado=None,
    )

    assert where_clause == "Filial = ?"
    assert params == ["02"]

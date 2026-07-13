from app.infrastructure.persistence.totvs.inspecoes_processo import (
    inspecoes_processo_repository as repo_module,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    _build_historico_list_filters,
)


def test_historico_list_sql_uses_two_step_tela_aggregation() -> None:
    source = open(repo_module.__file__, encoding="utf-8").read()
    assert "def list_historico_by_branch" in source
    assert "SELECT *" not in source
    assert "COUNT(*)" not in source

    list_method_start = source.index("def list_historico_by_branch")
    next_method = source.find("\n    def ", list_method_start + 1)
    list_method = source[list_method_start:next_method]
    assert "HISTORICO_TELA_VIEW" in list_method
    assert "_HISTORICO_TELA_LIST_SELECT" in list_method
    assert "GROUP BY Ordem_Producao" in list_method
    assert "GROUP BY Filial, Ordem_Producao" in list_method
    assert "POR_OP_VIEW" not in list_method
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" not in list_method
    assert "COUNT(DISTINCT Operacao)" not in source
    assert "COUNT(DISTINCT Matricula_Ensaiador)" not in source
    assert "UPPER(LTRIM(RTRIM(" not in source


def test_build_historico_list_filters_sargable_dates_in_where() -> None:
    where_clause, params = _build_historico_list_filters(
        "01",
        ordem_producao="10565201002",
        codigo_produto="90263652",
        data_inicio="2026-01-01",
        data_fim="2026-07-13",
    )
    assert "UPPER(" not in where_clause
    assert "Ordem_Producao LIKE ?" in where_clause
    assert "Codigo_Produto LIKE ?" in where_clause
    assert "Data_Medicao_Date >= ?" in where_clause
    assert "Data_Medicao_Date <= ?" in where_clause
    assert "HAVING" not in where_clause
    assert params == [
        "01",
        "10565201002%",
        "90263652%",
        "2026-01-01",
        "2026-07-13",
    ]


def test_historico_detalhe_sql_uses_historico_tela_with_filters() -> None:
    source = open(repo_module.__file__, encoding="utf-8").read()
    assert "vw_minha_delpi_inspecoes_processo_historico_tela" in source
    method_start = source.index("def list_historico_detalhe_itens_by_op")
    next_method = source.find("\n    def ", method_start + 1)
    method_body = source[method_start:] if next_method < 0 else source[method_start:next_method]
    assert "HISTORICO_TELA_VIEW" in method_body
    assert "Filial = ?" in method_body
    assert "Ordem_Producao" in method_body
    assert "SELECT TOP (" in method_body
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" not in method_body


def test_historico_cabecalho_aggregates_historico_tela() -> None:
    source = open(repo_module.__file__, encoding="utf-8").read()
    method_start = source.index("def get_historico_cabecalho_by_op")
    next_method = source.find("\n    def ", method_start + 1)
    method_body = source[method_start:next_method]
    assert "HISTORICO_TELA_VIEW" in method_body
    assert "_HISTORICO_TELA_LIST_SELECT" in method_body
    assert "GROUP BY Filial, Ordem_Producao" in method_body
    assert "POR_OP_VIEW" not in method_body
    assert "WITH (NOLOCK)" in method_body

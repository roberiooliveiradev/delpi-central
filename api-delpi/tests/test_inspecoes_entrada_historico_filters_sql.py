from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
    InspecoesEntradaHistoricoFilters,
)
from app.infrastructure.persistence.totvs.inspecoes_entrada.inspecoes_entrada_repository import (
    _build_historico_where,
)


def test_build_historico_where_uses_case_insensitive_supplier_filter() -> None:
    where_clause, params = _build_historico_where(
        "01",
        InspecoesEntradaHistoricoFilters(supplier="multiprint"),
    )

    assert "Nome_Fornecedor COLLATE Latin1_General_CI_AI LIKE ?" in where_clause
    assert params == ["01", "%multiprint%"]


def test_build_historico_where_uses_case_insensitive_inspector_filter() -> None:
    where_clause, params = _build_historico_where(
        "01",
        InspecoesEntradaHistoricoFilters(inspector="nathalia"),
    )

    assert "Nome_Ensaiador COLLATE Latin1_General_CI_AI LIKE ?" in where_clause
    assert params == ["01", "%nathalia%"]


def test_build_historico_where_uses_case_insensitive_exact_match_filters() -> None:
    where_clause, params = _build_historico_where(
        "01",
        InspecoesEntradaHistoricoFilters(
            product_code="10110388",
            invoice_number="000042999",
            lot="auto000952",
        ),
    )

    assert "UPPER(LTRIM(RTRIM(Codigo_Produto))) = UPPER(?)" in where_clause
    assert "UPPER(LTRIM(RTRIM(Nota_Fiscal))) = UPPER(?)" in where_clause
    assert "UPPER(LTRIM(RTRIM(Lote))) = UPPER(?)" in where_clause
    assert params == ["01", "10110388", "000042999", "auto000952"]

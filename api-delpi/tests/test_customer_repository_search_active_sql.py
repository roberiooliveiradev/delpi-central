"""Regressão SQL: busca de clientes para vínculo de carteira."""

from __future__ import annotations

from pathlib import Path


def _repository_source() -> str:
    root = Path(__file__).resolve().parents[1]
    return (
        root
        / "app/infrastructure/persistence/totvs/customer_repositories/customer_repository.py"
    ).read_text(encoding="utf-8")


def _method_source() -> str:
    src = _repository_source()
    return src.split("def search_active_customers", 1)[1].split(
        "def search_customers_by_query", 1
    )[0]


def test_search_active_customers_sql_matches_nreduz() -> None:
    """Busca deve achar nome fantasia e manter soft-delete sempre excluído."""
    method = _method_source()
    assert "A1_NREDUZ" in method
    assert "D_E_L_E_T_ = ''" in method
    assert "COALESCE" in method
    assert "NULLIF(LTRIM(RTRIM(SA1.A1_NREDUZ))" in method


def test_search_active_customers_blocked_filter_is_opt_in() -> None:
    """Bloqueio SA1 é condicional: default inclui (consulta), carteira exclui."""
    method = _method_source()
    assert "include_blocked: bool = True" in method
    assert "if not include_blocked" in method
    # NULL-safe: legado/NULL conta como ativo, não como bloqueado.
    assert "ISNULL(SA1.A1_MSBLQL, '') <> '1'" in method

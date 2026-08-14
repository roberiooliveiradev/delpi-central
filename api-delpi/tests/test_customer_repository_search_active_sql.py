"""Regressão SQL: busca de clientes para vínculo de carteira."""

from __future__ import annotations

from pathlib import Path


def _repository_source() -> str:
    root = Path(__file__).resolve().parents[1]
    return (
        root
        / "app/infrastructure/persistence/totvs/customer_repositories/customer_repository.py"
    ).read_text(encoding="utf-8")


def test_search_active_customers_sql_matches_nreduz_and_allows_blocked() -> None:
    """Gap «sem cobertura» usa pedidos; busca deve achar nome fantasia e bloqueados."""
    src = _repository_source()
    method = src.split("def search_active_customers", 1)[1].split(
        "def search_customers_by_query", 1
    )[0]
    assert "A1_NREDUZ" in method
    assert "A1_MSBLQL <> '1'" not in method
    assert "D_E_L_E_T_ = ''" in method
    assert "COALESCE" in method
    assert "NULLIF(LTRIM(RTRIM(SA1.A1_NREDUZ))" in method

"""Regressão: métricas de pedido aberto amarradas ao cadastro SA1."""

from __future__ import annotations

from pathlib import Path


def _repo_source() -> str:
    root = Path(__file__).resolve().parents[1]
    return (
        root
        / "app/infrastructure/persistence/totvs/pedidos_venda_abertos"
        / "pedidos_venda_abertos_query_repository.py"
    ).read_text(encoding="utf-8")


def test_aggregate_metrics_requires_sa1_customer_master() -> None:
    src = _repo_source()
    method = src.split("def aggregate_customer_open_order_metrics", 1)[1]
    assert "INNER JOIN SA1010" in method
    assert "A1_NREDUZ" in method
    assert "TRY_CAST" in method  # loja 1 vs 01

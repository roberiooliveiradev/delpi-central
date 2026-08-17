"""Tests for FIFO open-order stock allocation (parity with commercial MFE)."""

from __future__ import annotations

from commercial_app.domain.services.open_order_stock_allocation_service import (
    OpenOrderStockAllocationService,
    compare_lines_for_stock_allocation,
    round_quantity,
)


def test_round_quantity_three_decimals() -> None:
    assert round_quantity(1.2344) == 1.234
    assert round_quantity(1.2346) == 1.235
    assert round_quantity(None) == 0.0


def test_fifo_splits_shared_physical_stock_across_competing_lines() -> None:
    """Same product/branch: stock covers only the earliest delivery line."""
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "200",
            "linha": "01",
            "saldo": 10,
            "no_estoque": 10,
            "data_entrega": "2026-09-15",
        },
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "100",
            "linha": "01",
            "saldo": 10,
            "no_estoque": 10,
            "data_entrega": "2026-09-01",
        },
    ]
    allocated = OpenOrderStockAllocationService().allocate(items)
    by_pedido = {item["pedido"]: item["estoque_alocado"] for item in allocated}
    assert by_pedido["100"] == 10.0
    assert by_pedido["200"] == 0.0


def test_allocation_preserves_input_order() -> None:
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "B",
            "linha": "01",
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-10-01",
        },
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "A",
            "linha": "01",
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-09-01",
        },
    ]
    allocated = OpenOrderStockAllocationService().allocate(items)
    assert [item["pedido"] for item in allocated] == ["B", "A"]
    assert allocated[0]["estoque_alocado"] == 0.0
    assert allocated[1]["estoque_alocado"] == 5.0


def test_different_products_do_not_share_stock() -> None:
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "1",
            "linha": "01",
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-09-01",
        },
        {
            "filial": "01",
            "produto": "P2",
            "pedido": "2",
            "linha": "01",
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-09-01",
        },
    ]
    allocated = OpenOrderStockAllocationService().allocate(items)
    assert all(item["estoque_alocado"] == 5.0 for item in allocated)


def test_compare_empty_delivery_sorts_after_dated() -> None:
    dated = {"data_entrega": "2026-09-01", "pedido": "A", "linha": "01"}
    undated = {"data_entrega": "", "pedido": "A", "linha": "01"}
    assert compare_lines_for_stock_allocation(dated, undated) < 0
    assert compare_lines_for_stock_allocation(undated, dated) > 0

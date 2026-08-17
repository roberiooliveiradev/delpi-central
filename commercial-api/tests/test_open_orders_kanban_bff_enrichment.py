"""Regression: kanban enrichment allocates FIFO before stage counts (badge parity)."""

from __future__ import annotations

from commercial_app.application.services.enrich_open_orders_kanban_service import (
    EnrichOpenOrdersKanbanService,
)
from commercial_app.domain.services.open_order_kanban_stage_service import (
    STAGE_IN_PROGRESS,
    STAGE_READY_TO_INVOICE,
    STAGE_UPCOMING,
)


def _ready_count(counts: dict) -> int:
    for stage in counts.get("stages") or []:
        if stage.get("id") == STAGE_READY_TO_INVOICE:
            return int(stage.get("lineCount") or 0)
    return 0


def test_bff_enrichment_shape_for_open_orders_payload() -> None:
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "1",
            "linha": "01",
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-09-01",
            "valor_aberto": 10,
        }
    ]
    payload = EnrichOpenOrdersKanbanService().build_payload_fields(items)
    assert payload["items"][0]["kanbanStage"] == STAGE_READY_TO_INVOICE
    assert payload["items"][0]["estoque_alocado"] == 5.0
    assert "deliveryHorizon" in payload
    assert _ready_count(payload["kanbanStageCounts"]) == 1


def test_fifo_prevents_double_counting_ready_to_invoice_for_shared_stock() -> None:
    """Causa raiz do badge 58 vs chip 36: sem FIFO, ambas linhas contavam como ready."""
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "LATE",
            "linha": "01",
            "saldo": 10,
            "no_estoque": 10,
            "data_entrega": "2026-10-01",
            "valor_aberto": 100,
        },
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "EARLY",
            "linha": "01",
            "saldo": 10,
            "no_estoque": 10,
            "data_entrega": "2026-09-01",
            "valor_aberto": 100,
        },
    ]
    payload = EnrichOpenOrdersKanbanService().build_payload_fields(
        items,
        as_of=__import__("datetime").date(2026, 8, 17),
    )
    by_pedido = {item["pedido"]: item for item in payload["items"]}
    assert by_pedido["EARLY"]["estoque_alocado"] == 10.0
    assert by_pedido["EARLY"]["kanbanStage"] == STAGE_READY_TO_INVOICE
    assert by_pedido["LATE"]["estoque_alocado"] == 0.0
    assert by_pedido["LATE"]["kanbanStage"] == STAGE_UPCOMING
    assert _ready_count(payload["kanbanStageCounts"]) == 1


def test_partial_after_fifo_is_in_progress() -> None:
    items = [
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "A",
            "linha": "01",
            "saldo": 8,
            "no_estoque": 10,
            "data_entrega": "2026-09-01",
            "valor_aberto": 80,
        },
        {
            "filial": "01",
            "produto": "P1",
            "pedido": "B",
            "linha": "01",
            "saldo": 8,
            "no_estoque": 10,
            "data_entrega": "2026-09-15",
            "valor_aberto": 80,
        },
    ]
    payload = EnrichOpenOrdersKanbanService().build_payload_fields(
        items,
        as_of=__import__("datetime").date(2026, 8, 17),
    )
    by_pedido = {item["pedido"]: item for item in payload["items"]}
    assert by_pedido["A"]["estoque_alocado"] == 8.0
    assert by_pedido["A"]["kanbanStage"] == STAGE_READY_TO_INVOICE
    assert by_pedido["B"]["estoque_alocado"] == 2.0
    assert by_pedido["B"]["kanbanStage"] == STAGE_IN_PROGRESS
    assert _ready_count(payload["kanbanStageCounts"]) == 1

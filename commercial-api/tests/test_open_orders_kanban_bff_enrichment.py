"""Regression: list open-orders BFF attaches kanbanStage + counts."""

from __future__ import annotations

from commercial_app.domain.services.open_order_kanban_stage_service import (
    STAGE_READY_TO_INVOICE,
    OpenOrderKanbanStageService,
)


def test_bff_enrichment_shape_for_open_orders_payload() -> None:
    """Mirrors the enrich block in list_commercial_open_orders (route wiring)."""
    items = [
        {
            "saldo": 5,
            "no_estoque": 5,
            "data_entrega": "2026-09-01",
            "valor_aberto": 10,
        }
    ]
    svc = OpenOrderKanbanStageService()
    enriched = svc.enrich_items(items)
    counts = svc.count_by_stage(enriched)
    assert enriched[0]["kanbanStage"] == STAGE_READY_TO_INVOICE
    assert "stages" in counts
    assert any(s["id"] == STAGE_READY_TO_INVOICE and s["lineCount"] == 1 for s in counts["stages"])

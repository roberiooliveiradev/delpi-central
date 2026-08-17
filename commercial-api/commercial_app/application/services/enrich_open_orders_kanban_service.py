"""Orchestrate FIFO stock allocation + kanban stage enrichment for open orders.

Single entry point for BFF list and any consumer that needs ``kanbanStage`` /
``kanbanStageCounts`` aligned with the MFE «Pode faturar» rule.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from commercial_app.domain.services.open_order_kanban_stage_service import (
    OpenOrderKanbanStageService,
)
from commercial_app.domain.services.open_order_stock_allocation_service import (
    OpenOrderStockAllocationService,
)
from commercial_app.domain.services.open_orders_horizon_bucket_service import (
    OpenOrdersHorizonBucketService,
)


class EnrichOpenOrdersKanbanService:
    """allocate stock → enrich stages → counts (+ optional delivery horizon)."""

    def __init__(
        self,
        *,
        allocation_service: OpenOrderStockAllocationService | None = None,
        stage_service: OpenOrderKanbanStageService | None = None,
        horizon_service: OpenOrdersHorizonBucketService | None = None,
    ) -> None:
        self._allocation = allocation_service or OpenOrderStockAllocationService()
        self._stages = stage_service or OpenOrderKanbanStageService()
        self._horizon = horizon_service or OpenOrdersHorizonBucketService()

    def enrich_items(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of=None,
    ) -> list[dict[str, Any]]:
        allocated = self._allocation.allocate(items)
        return self._stages.enrich_items(allocated, as_of=as_of)

    def build_payload_fields(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of=None,
        include_horizon: bool = True,
    ) -> dict[str, Any]:
        enriched = self.enrich_items(items, as_of=as_of)
        payload: dict[str, Any] = {
            "items": enriched,
            "kanbanStageCounts": self._stages.count_by_stage(enriched, as_of=as_of),
        }
        if include_horizon:
            payload["deliveryHorizon"] = self._horizon.bucketize(enriched)
        return payload

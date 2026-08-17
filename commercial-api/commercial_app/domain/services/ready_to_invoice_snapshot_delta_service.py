"""Detect open-order lines that newly entered ready_to_invoice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from commercial_app.domain.services.open_order_kanban_stage_service import (
    STAGE_READY_TO_INVOICE,
    OpenOrderKanbanStageService,
)


def open_order_line_key(item: Mapping[str, Any]) -> str:
    filial = str(item.get("filial") or "").strip()
    pedido = str(item.get("pedido") or "").strip()
    linha = str(item.get("linha") or "").strip()
    return f"{filial}|{pedido}|{linha}"


@dataclass(frozen=True, slots=True)
class ReadyToInvoiceDelta:
    previous_keys: frozenset[str]
    current_keys: frozenset[str]
    entered_keys: frozenset[str]
    entered_items: tuple[dict[str, Any], ...]


class ReadyToInvoiceSnapshotDeltaService:
    """Compare current ready_to_invoice keys vs previous snapshot (pure)."""

    def __init__(self, stage_service: OpenOrderKanbanStageService | None = None) -> None:
        self._stages = stage_service or OpenOrderKanbanStageService()

    def current_ready_items(
        self,
        items: Sequence[Mapping[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        ready: list[dict[str, Any]] = []
        for raw in items or ():
            item = dict(raw)
            stage = self._stages.resolve_stage(item)
            if stage != STAGE_READY_TO_INVOICE:
                continue
            item["kanbanStage"] = STAGE_READY_TO_INVOICE
            key = open_order_line_key(item)
            if not key or key == "||":
                continue
            item["_lineKey"] = key
            ready.append(item)
        return ready

    def compute_delta(
        self,
        *,
        items: Sequence[Mapping[str, Any]] | None,
        previous_keys: Sequence[str] | None,
    ) -> ReadyToInvoiceDelta:
        previous = frozenset(
            str(key).strip() for key in (previous_keys or ()) if str(key).strip()
        )
        ready_items = self.current_ready_items(items)
        current = frozenset(str(item["_lineKey"]) for item in ready_items)
        entered = current - previous
        entered_items = tuple(
            item for item in ready_items if item["_lineKey"] in entered
        )
        return ReadyToInvoiceDelta(
            previous_keys=previous,
            current_keys=current,
            entered_keys=entered,
            entered_items=entered_items,
        )

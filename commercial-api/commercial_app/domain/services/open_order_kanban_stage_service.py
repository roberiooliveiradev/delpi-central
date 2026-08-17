"""Classify open-order lines into Kanban stages (read-only board columns).

Stages (mutually exclusive for open lines):
- ready_to_invoice: allocated stock >= saldo
- in_progress: overdue delivery or partial stock
- upcoming: remaining open lines

``completed`` is fed by a separate recently-closed list, not this service.

Callers that build ``kanbanStageCounts`` for the portal badge must run
``OpenOrderStockAllocationService`` first (via ``EnrichOpenOrdersKanbanService``)
so ``estoque_alocado`` reflects FIFO across lines that share physical stock.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Mapping, Sequence
from zoneinfo import ZoneInfo

KanbanStage = Literal["upcoming", "in_progress", "ready_to_invoice"]

STAGE_UPCOMING: KanbanStage = "upcoming"
STAGE_IN_PROGRESS: KanbanStage = "in_progress"
STAGE_READY_TO_INVOICE: KanbanStage = "ready_to_invoice"

OPEN_STAGES: tuple[KanbanStage, ...] = (
    STAGE_UPCOMING,
    STAGE_IN_PROGRESS,
    STAGE_READY_TO_INVOICE,
)

KANBAN_TIMEZONE = "America/Sao_Paulo"


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_delivery_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _allocated_stock(item: Mapping[str, Any]) -> float:
    if "estoque_alocado" in item and item.get("estoque_alocado") is not None:
        return _as_float(item.get("estoque_alocado"))
    return _as_float(item.get("no_estoque"))


class OpenOrderKanbanStageService:
    """Pure stage resolution from open-order line fields (no OP / factory)."""

    def resolve_stage(
        self,
        item: Mapping[str, Any],
        *,
        as_of: date | None = None,
        timezone_name: str = KANBAN_TIMEZONE,
    ) -> KanbanStage:
        today = as_of
        if today is None:
            today = datetime.now(ZoneInfo(timezone_name)).date()

        saldo = _as_float(item.get("saldo"))
        stock = _allocated_stock(item)

        if saldo > 0 and stock >= saldo:
            return STAGE_READY_TO_INVOICE

        delivery = _parse_delivery_date(item.get("data_entrega"))
        overdue = bool(delivery and saldo > 0 and delivery < today)
        partial = saldo > 0 and stock > 0 and stock < saldo
        if overdue or partial:
            return STAGE_IN_PROGRESS

        return STAGE_UPCOMING

    def enrich_items(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of: date | None = None,
        timezone_name: str = KANBAN_TIMEZONE,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for raw in items or ():
            item = dict(raw)
            item["kanbanStage"] = self.resolve_stage(
                item, as_of=as_of, timezone_name=timezone_name
            )
            out.append(item)
        return out

    def count_by_stage(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of: date | None = None,
        timezone_name: str = KANBAN_TIMEZONE,
    ) -> dict[str, Any]:
        counts = {stage: {"lineCount": 0, "openValue": 0.0} for stage in OPEN_STAGES}
        for raw in items or ():
            stage = self.resolve_stage(raw, as_of=as_of, timezone_name=timezone_name)
            counts[stage]["lineCount"] += 1
            counts[stage]["openValue"] += _as_float(raw.get("valor_aberto"))
        return {
            "stages": [
                {
                    "id": stage,
                    "lineCount": counts[stage]["lineCount"],
                    "openValue": counts[stage]["openValue"],
                }
                for stage in OPEN_STAGES
            ]
        }

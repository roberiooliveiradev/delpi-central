"""Tests for OpenOrderKanbanStageService — mutually exclusive open stages."""

from __future__ import annotations

from datetime import date

from commercial_app.domain.services.open_order_kanban_stage_service import (
    STAGE_IN_PROGRESS,
    STAGE_READY_TO_INVOICE,
    STAGE_UPCOMING,
    OpenOrderKanbanStageService,
)

AS_OF = date(2026, 8, 14)


def _item(**kwargs):
    base = {
        "filial": "01",
        "pedido": "100",
        "linha": "01",
        "saldo": 10.0,
        "no_estoque": 0.0,
        "data_entrega": "2026-09-01",
        "valor_aberto": 100.0,
    }
    base.update(kwargs)
    return base


def test_ready_to_invoice_when_stock_covers_saldo() -> None:
    svc = OpenOrderKanbanStageService()
    assert svc.resolve_stage(_item(no_estoque=10), as_of=AS_OF) == STAGE_READY_TO_INVOICE
    assert (
        svc.resolve_stage(_item(no_estoque=15, data_entrega="2026-01-01"), as_of=AS_OF)
        == STAGE_READY_TO_INVOICE
    )


def test_ready_prefers_estoque_alocado_over_no_estoque() -> None:
    svc = OpenOrderKanbanStageService()
    assert (
        svc.resolve_stage(_item(no_estoque=0, estoque_alocado=10), as_of=AS_OF)
        == STAGE_READY_TO_INVOICE
    )


def test_in_progress_when_overdue_without_full_stock() -> None:
    svc = OpenOrderKanbanStageService()
    assert (
        svc.resolve_stage(_item(data_entrega="2026-08-01", no_estoque=0), as_of=AS_OF)
        == STAGE_IN_PROGRESS
    )
    assert (
        svc.resolve_stage(_item(data_entrega="2026-08-01", no_estoque=3), as_of=AS_OF)
        == STAGE_IN_PROGRESS
    )


def test_in_progress_when_partial_stock_not_overdue() -> None:
    svc = OpenOrderKanbanStageService()
    assert (
        svc.resolve_stage(_item(no_estoque=4, data_entrega="2026-09-01"), as_of=AS_OF)
        == STAGE_IN_PROGRESS
    )


def test_upcoming_when_future_and_no_stock() -> None:
    svc = OpenOrderKanbanStageService()
    assert (
        svc.resolve_stage(_item(no_estoque=0, data_entrega="2026-09-01"), as_of=AS_OF)
        == STAGE_UPCOMING
    )


def test_stages_are_mutually_exclusive_for_fixture_set() -> None:
    svc = OpenOrderKanbanStageService()
    fixtures = [
        _item(no_estoque=10),
        _item(no_estoque=0, data_entrega="2026-08-01"),
        _item(no_estoque=3),
        _item(no_estoque=0, data_entrega="2026-10-01"),
    ]
    stages = {svc.resolve_stage(f, as_of=AS_OF) for f in fixtures}
    assert stages == {STAGE_READY_TO_INVOICE, STAGE_IN_PROGRESS, STAGE_UPCOMING}
    for f in fixtures:
        assert svc.resolve_stage(f, as_of=AS_OF) in (
            STAGE_UPCOMING,
            STAGE_IN_PROGRESS,
            STAGE_READY_TO_INVOICE,
        )


def test_enrich_and_count_by_stage() -> None:
    svc = OpenOrderKanbanStageService()
    items = [
        _item(no_estoque=10, valor_aberto=50),
        _item(no_estoque=0, data_entrega="2026-08-01", valor_aberto=20),
        _item(no_estoque=0, data_entrega="2026-10-01", valor_aberto=30),
    ]
    enriched = svc.enrich_items(items, as_of=AS_OF)
    assert [i["kanbanStage"] for i in enriched] == [
        STAGE_READY_TO_INVOICE,
        STAGE_IN_PROGRESS,
        STAGE_UPCOMING,
    ]
    counts = svc.count_by_stage(items, as_of=AS_OF)
    by_id = {s["id"]: s for s in counts["stages"]}
    assert by_id[STAGE_READY_TO_INVOICE]["lineCount"] == 1
    assert by_id[STAGE_READY_TO_INVOICE]["openValue"] == 50.0
    assert by_id[STAGE_IN_PROGRESS]["lineCount"] == 1
    assert by_id[STAGE_UPCOMING]["lineCount"] == 1
    assert by_id[STAGE_UPCOMING]["openValue"] == 30.0

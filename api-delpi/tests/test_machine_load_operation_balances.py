"""Unit — use case de saldos SH6/SC2 por operação da carga máquina (sem HZA)."""

from __future__ import annotations

from typing import Any

from app.application.use_cases.production.get_production_machine_load_use_cases import (
    GetProductionMachineLoadOperationBalancesUseCase,
)


class FakeRepo:
    def __init__(
        self,
        *,
        finish_rows: list[dict[str, Any]] | None = None,
        produced_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.finish_rows = finish_rows or []
        self.produced_rows = produced_rows or []
        self.finish_calls: list[dict[str, Any]] = []
        self.produced_calls: list[dict[str, Any]] = []
        self.hza_calls = 0

    def get_order_finish_flags(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.finish_calls.append(kwargs)
        return self.finish_rows

    def get_operation_produced_qty(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.produced_calls.append(kwargs)
        return self.produced_rows

    def get_appointment_status(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.hza_calls += 1
        return []


def test_balances_return_produced_and_pending_per_operation() -> None:
    repo = FakeRepo(
        finish_rows=[
            {
                "production_order": "10964501004",
                "is_finished": 0,
                "finish_date": None,
                "planned_qty": 7.8,
                "pending_qty": 6.3,
            }
        ],
        produced_rows=[
            {
                "production_order": "10964501004",
                "operation_code": "01",
                "operation_produced_qty": 3.0,
            }
        ],
    )
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10964501004", "operation_code": "01"}],
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] == 3.0
    assert item["operation_pending_qty"] == 4.8
    assert repo.hza_calls == 0
    assert repo.produced_calls[0]["production_orders"] == ["10964501004"]


def test_operation_without_sh6_row_gets_full_operation_balance() -> None:
    """Operação coberta pela consulta e sem linha na SH6 tem produzido zero."""
    repo = FakeRepo(
        finish_rows=[
            {
                "production_order": "10964501004",
                "is_finished": 0,
                "finish_date": None,
                "planned_qty": 7.8,
                "pending_qty": 6.3,
            }
        ],
        produced_rows=[
            {
                "production_order": "10964501004",
                "operation_code": "01",
                "operation_produced_qty": 7.8,
            }
        ],
    )
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10964501004", "operation_code": "03"}],
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] == 0.0
    assert item["operation_pending_qty"] == 7.8


def test_finished_order_zeroes_operation_balance() -> None:
    """C2_DATRF preenchida: saldo da operação vai a zero."""
    repo = FakeRepo(
        finish_rows=[
            {
                "production_order": "10846301001",
                "is_finished": 1,
                "finish_date": "20260815",
                "planned_qty": 10.0,
                "pending_qty": 0.0,
            }
        ],
        produced_rows=[
            {
                "production_order": "10846301001",
                "operation_code": "01",
                "operation_produced_qty": 4.0,
            }
        ],
    )
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "10846301001", "operation_code": "01"}],
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] == 4.0
    assert item["operation_pending_qty"] == 0.0


def test_partial_appointment_keeps_remaining_balance() -> None:
    """Apontamento parcial: saldo da operação permanece positivo."""
    repo = FakeRepo(
        finish_rows=[
            {
                "production_order": "OP1",
                "is_finished": 0,
                "finish_date": None,
                "planned_qty": 10.0,
                "pending_qty": 4.0,
            }
        ],
        produced_rows=[
            {
                "production_order": "OP1",
                "operation_code": "01",
                "operation_produced_qty": 6.0,
            }
        ],
    )
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "OP1", "operation_code": "01"}],
    )
    assert result["items"][0]["operation_pending_qty"] == 4.0


def test_duplicate_items_are_deduplicated() -> None:
    repo = FakeRepo()
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="01",
        items=[
            {"production_order": "OP1", "operation_code": "01"},
            {"production_order": "OP1", "operation_code": "01"},
            {"production_order": "OP2", "operation_code": "01"},
        ],
    )
    assert len(result["items"]) == 2
    assert result["summary"]["requested_count"] == 2


def test_order_chunking_respects_sql_parameter_limit() -> None:
    """Lotes de 500 OPs por consulta — teto de parâmetros do SQL Server."""
    repo = FakeRepo()
    orders = [f"OP{i:05d}" for i in range(1200)]
    GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="01",
        items=[{"production_order": order, "operation_code": "01"} for order in orders],
    )
    assert len(repo.finish_calls) == 3
    assert len(repo.produced_calls) == 3
    for call in repo.finish_calls:
        assert len(call["production_orders"]) <= 500


def test_repository_without_balance_methods_returns_null_fields() -> None:
    """Repositório legado sem SH6/SC2 não quebra — saldo desconhecido é None."""

    class LegacyRepo:
        pass

    result = GetProductionMachineLoadOperationBalancesUseCase(LegacyRepo()).execute(
        branch="01",
        items=[{"production_order": "OP1", "operation_code": "01"}],
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] is None
    assert item["operation_pending_qty"] is None


def test_empty_items_returns_empty_items() -> None:
    repo = FakeRepo()
    result = GetProductionMachineLoadOperationBalancesUseCase(repo).execute(
        branch="01", items=[]
    )
    assert result["items"] == []
    assert repo.finish_calls == []
    assert repo.produced_calls == []

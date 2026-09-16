"""Unit — use case de status de apontamento da carga máquina."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.use_cases.production.get_production_machine_load_use_cases import (
    GetProductionMachineLoadAppointmentStatusUseCase,
)


class FakeRepo:
    def __init__(
        self,
        rows: list[dict[str, Any]],
        *,
        finish_rows: list[dict[str, Any]] | None = None,
        produced_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.rows = rows
        self.finish_rows = finish_rows or []
        self.produced_rows = produced_rows or []
        self.calls: list[dict[str, Any]] = []
        self.finish_calls: list[dict[str, Any]] = []
        self.produced_calls: list[dict[str, Any]] = []

    def get_appointment_status(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return self.rows

    def get_order_finish_flags(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.finish_calls.append(kwargs)
        return self.finish_rows

    def get_operation_produced_qty(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.produced_calls.append(kwargs)
        return self.produced_rows


def test_appointment_status_filters_to_requested_keys() -> None:
    repo = FakeRepo(
        [
            {
                "branch": "02",
                "production_order": "10808301002",
                "operation_code": "01",
                "active_appointment_count": 1,
                "active_operator_count": 1,
                "active_marker": "2026081918:58:25000223SILVANA",
                "appointment_count": 2,
                "last_appointment_date": "20260819",
            },
            {
                "branch": "02",
                "production_order": "99999901001",
                "operation_code": "01",
                "active_appointment_count": 0,
                "active_operator_count": 0,
                "active_marker": "",
                "appointment_count": 1,
                "last_appointment_date": "20260810",
            },
        ]
    )
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10808301002", "operation_code": "01"}],
        today=date(2026, 8, 19),
    )
    assert len(result["items"]) == 1
    assert result["items"][0]["is_in_production"] is True
    assert result["summary"]["in_production_count"] == 1
    assert repo.calls[0]["appointment_active_since"] == "20260817"


def test_missing_key_returns_not_started() -> None:
    repo = FakeRepo([])
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "111", "operation_code": "01"}],
        today=date(2026, 8, 19),
    )
    assert result["items"][0]["production_status"] == "not_started"
    assert result["items"][0]["is_in_production"] is False


def test_finished_order_without_recent_hza_is_started() -> None:
    """C2_DATRF preenchida: permanece na fila congelada como «Já apontada»."""
    repo = FakeRepo(
        [],
        finish_rows=[
            {
                "production_order": "10846301001",
                "is_finished": 1,
                "finish_date": "20260815",
            }
        ],
    )
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "10846301001", "operation_code": "01"}],
        today=date(2026, 8, 21),
    )
    item = result["items"][0]
    assert item["production_status"] == "started"
    assert item["is_in_production"] is False
    assert item["production_started_date"] == "2026-08-15"
    assert repo.finish_calls[0]["production_orders"] == ["10846301001"]


def test_finished_order_with_open_appointment_is_started() -> None:
    """Coletor não encerrado não mantém OP encerrada como «Em produção»."""
    repo = FakeRepo(
        [
            {
                "branch": "01",
                "production_order": "10846301001",
                "operation_code": "01",
                "active_appointment_count": 1,
                "active_operator_count": 1,
                "active_marker": "2026082115:31:53000311CARLA SOARES DE JESUS",
                "last_marker": "2026082115:31:53000311CARLA SOARES DE JESUS",
                "appointment_count": 4,
                "last_appointment_date": "20260821",
            }
        ],
        finish_rows=[
            {
                "production_order": "10846301001",
                "is_finished": 1,
                "finish_date": "20260821",
            }
        ],
    )
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "10846301001", "operation_code": "01"}],
        today=date(2026, 8, 21),
    )
    item = result["items"][0]
    assert item["is_in_production"] is False
    assert item["production_status"] == "started"
    assert item["active_operator_count"] == 0
    # O operador e a hora do último apontamento continuam visíveis na fila.
    assert item["active_operator_name"] == "CARLA SOARES DE JESUS"
    assert item["production_started_time"] == "15:31:53"
    assert result["summary"]["in_production_count"] == 0


def test_operation_without_balance_is_started_even_with_order_balance() -> None:
    """Caso real: operação 01 apontada por inteiro numa OP que ainda tem saldo."""
    repo = FakeRepo(
        [
            {
                "branch": "02",
                "production_order": "10964501004",
                "operation_code": "01",
                "active_appointment_count": 1,
                "active_operator_count": 1,
                "active_marker": "2026091605:12:44000311CARLA SOARES DE JESUS",
                "last_marker": "2026091605:12:44000311CARLA SOARES DE JESUS",
                "appointment_count": 4,
                "last_appointment_date": "20260916",
            }
        ],
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
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10964501004", "operation_code": "01"}],
        today=date(2026, 9, 16),
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] == 7.8
    assert item["operation_pending_qty"] == 0.0
    assert item["is_in_production"] is False
    assert item["production_status"] == "started"
    assert result["summary"]["in_production_count"] == 0
    assert repo.produced_calls[0]["production_orders"] == ["10964501004"]


def test_operation_without_appointment_row_gets_full_operation_balance() -> None:
    """Operação coberta pela consulta e sem linha na SH6 tem produzido zero."""
    repo = FakeRepo(
        [],
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
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10964501004", "operation_code": "03"}],
        today=date(2026, 9, 16),
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] == 0.0
    assert item["operation_pending_qty"] == 7.8
    assert item["production_status"] == "not_started"


def test_repository_without_operation_balance_keeps_header_rule() -> None:
    """Repositório antigo (sem o agregado da SH6) não perde o comportamento atual."""

    class LegacyRepo:
        def get_appointment_status(self, **_kwargs: Any) -> list[dict[str, Any]]:
            return []

        def get_order_finish_flags(self, **_kwargs: Any) -> list[dict[str, Any]]:
            return [
                {
                    "production_order": "10964501004",
                    "is_finished": 0,
                    "finish_date": None,
                    "planned_qty": 7.8,
                    "pending_qty": 6.3,
                }
            ]

    repo = LegacyRepo()
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="02",
        items=[{"production_order": "10964501004", "operation_code": "01"}],
        today=date(2026, 9, 16),
    )
    item = result["items"][0]
    assert item["operation_produced_qty"] is None
    assert item["operation_pending_qty"] is None


def test_zero_pending_with_open_appointment_is_started() -> None:
    """Saldo SC2 zerado derruba «Em produção» mesmo sem C2_DATRF."""
    repo = FakeRepo(
        [
            {
                "branch": "01",
                "production_order": "10846301001",
                "operation_code": "01",
                "active_appointment_count": 1,
                "active_operator_count": 1,
                "active_marker": "2026082115:31:53000311CARLA SOARES DE JESUS",
                "last_marker": "2026082115:31:53000311CARLA SOARES DE JESUS",
                "appointment_count": 2,
                "last_appointment_date": "20260821",
            }
        ],
        finish_rows=[
            {
                "production_order": "10846301001",
                "is_finished": 0,
                "finish_date": None,
                "pending_qty": 0,
            }
        ],
    )
    result = GetProductionMachineLoadAppointmentStatusUseCase(repo).execute(
        branch="01",
        items=[{"production_order": "10846301001", "operation_code": "01"}],
        today=date(2026, 8, 21),
    )
    item = result["items"][0]
    assert item["is_in_production"] is False
    assert item["production_status"] == "started"
    assert result["summary"]["in_production_count"] == 0

"""Unit — histórico público de apontamentos da OP+operação."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_operation_appointments_service import (
    PublicOperationAppointmentsService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.rows = rows or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def fetch_production_appointments(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise DelpiGatewayError("api-delpi fora.")
        return {"success": True, "data": {"items": self.rows}}


class FakeMachineLoad:
    def __init__(
        self,
        *,
        contains: bool = True,
        balance: dict[str, float | None] | None = None,
    ) -> None:
        self.contains = contains
        self.balance = balance
        self.calls: list[dict[str, Any]] = []
        self.balance_calls: list[dict[str, Any]] = []

    def public_snapshot_contains_operation(self, **kwargs: Any) -> bool:
        self.calls.append(kwargs)
        return self.contains

    def public_operation_balance(self, **kwargs: Any) -> dict[str, float | None] | None:
        self.balance_calls.append(kwargs)
        return self.balance if self.contains else None


def _service(
    gateway: FakeGateway,
    *,
    machine_load: FakeMachineLoad | None = None,
) -> PublicOperationAppointmentsService:
    return PublicOperationAppointmentsService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
        clock=lambda: datetime(2026, 9, 16, 12, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def test_lists_appointments_for_operation_newest_first() -> None:
    gateway = FakeGateway(
        [
            {
                "production_order": "10964501004",
                "operation": "01",
                "work_center": "CT-01A",
                "appointment_date": "20260910",
                "start_time": "08:00",
                "end_time": "09:00",
                "qty_produced": 2.2,
                "unit": "MI",
                "operator_name": "JOAO",
                "operator_code": "0001",
            },
            {
                "production_order": "10964501004",
                "operation": "01",
                "work_center": "CT-00",
                "appointment_date": "20260913",
                "start_time": "21:00",
                "end_time": "22:00",
                # API de apontamentos normaliza MI→UN; cockpit reconverte para MI.
                "qty_produced": 5600.0,
                "unit": "UN",
                "operator_name": "ANDIA GOMES GONCALVES",
            },
            {
                "production_order": "10964501004",
                "operation": "02",
                "work_center": "CT-00",
                "appointment_date": "20260912",
                "start_time": "14:00",
                "qty_produced": 1500.0,
                "unit": "UN",
                "operator_name": "OP 02 IRREGULAR",
            },
            {
                "production_order": "10964501004",
                "operation": "02",
                "work_center": "CT-01A",
                "appointment_date": "20260914",
                "start_time": "10:00",
                "qty_produced": 9.0,
                "unit": "MI",
                "operator_name": "OUTRA OP",
            },
        ]
    )
    payload = _service(gateway).list_for_operation(
        token=_token(),
        branch="02",
        production_order="10964501004",
        operation_code="01",
    )

    assert gateway.calls[0]["op"] == "10964501004"
    assert payload["summary"]["appointment_count"] == 2
    assert payload["summary"]["produced_qty"] == 7.8
    assert [item["produced_on"] for item in payload["items"]] == [
        "2026-09-13",
        "2026-09-10",
    ]
    assert payload["items"][0]["operator_name"] == "ANDIA GOMES GONCALVES"
    assert payload["items"][0]["quantity"] == 5.6
    assert payload["items"][0]["work_center"] == "CT-00"
    assert payload["items"][0]["unit"] == "MI"
    assert "login" not in str(payload["items"][0]).lower()
    assert "operator_code" not in payload["items"][0]


def test_total_comes_from_operation_balance_not_history_window() -> None:
    """Apontamento fora da janela não pode encolher o total da operação."""
    gateway = FakeGateway(
        [
            {
                "production_order": "10964501004",
                "operation": "01",
                "work_center": "CT-01A",
                "appointment_date": "20260910",
                "start_time": "08:00",
                "qty_produced": 2.2,
                "unit": "MI",
                "operator_name": "JOAO",
            },
        ]
    )
    machine_load = FakeMachineLoad(
        balance={"operation_produced_qty": 7.8, "operation_pending_qty": 0.0}
    )
    payload = _service(gateway, machine_load=machine_load).list_for_operation(
        token=_token(),
        branch="02",
        production_order="10964501004",
        operation_code="01",
    )

    assert payload["summary"]["produced_qty"] == 7.8
    assert payload["summary"]["window_produced_qty"] == 2.2
    assert payload["summary"]["pending_qty"] == 0.0
    assert payload["summary"]["appointment_count"] == 1


def test_rejects_invalid_token() -> None:
    with pytest.raises(PublicAccessDenied):
        _service(FakeGateway()).list_for_operation(
            token="invalido",
            branch="02",
            production_order="10964501004",
            operation_code="01",
        )


def test_rejects_operation_outside_published_queue() -> None:
    with pytest.raises(ValueError, match="fila publicada"):
        _service(FakeGateway(), machine_load=FakeMachineLoad(contains=False)).list_for_operation(
            token=_token(),
            branch="02",
            production_order="10964501004",
            operation_code="01",
        )


def test_propagates_gateway_failure() -> None:
    with pytest.raises(DelpiGatewayError):
        _service(FakeGateway(fail=True)).list_for_operation(
            token=_token(),
            branch="02",
            production_order="10964501004",
            operation_code="01",
        )

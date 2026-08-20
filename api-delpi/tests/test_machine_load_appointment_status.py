"""Unit — use case de status de apontamento da carga máquina."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.use_cases.production.get_production_machine_load_use_cases import (
    GetProductionMachineLoadAppointmentStatusUseCase,
)


class FakeRepo:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, Any]] = []

    def get_appointment_status(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return self.rows


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

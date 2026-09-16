"""Unit — paradas do turno no posto (modal do cockpit público)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_work_center_downtime_items_service import (
    PublicWorkCenterDowntimeItemsService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.rows = rows or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def fetch_factory_shifts(self) -> dict[str, Any]:
        return {
            "success": True,
            "data": {
                "current_shift": {
                    "id": "2",
                    "label": "2º turno",
                    "start_time": "14:10",
                    "end_time": "22:30",
                }
            },
        }

    def fetch_unproductive_hours_items(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise DelpiGatewayError("api-delpi fora.")
        return {"success": True, "data": {"items": self.rows}}


class FakeMachineLoad:
    def __init__(self, resources: list[str] | None = None) -> None:
        self.resources = resources
        self.calls: list[dict[str, Any]] = []

    def public_snapshot_work_center_resources(self, **kwargs: Any) -> list[str] | None:
        self.calls.append(kwargs)
        return self.resources


def _service(
    gateway: FakeGateway,
    *,
    machine_load: FakeMachineLoad | None = None,
) -> PublicWorkCenterDowntimeItemsService:
    return PublicWorkCenterDowntimeItemsService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=machine_load
        or FakeMachineLoad(["MAQ01", "MAQ02"]),
        branch_access=BranchAccessService(),
        clock=lambda: datetime(2026, 9, 16, 16, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def test_lists_today_shift_downtime_with_reason_and_observation() -> None:
    gateway = FakeGateway(
        [
            {
                "reference_date": "2026-09-16",
                "production_order": "10916601005",
                "operation": "01",
                "resource": "MAQ01",
                "operator_name": "JOAO",
                "operator_code": "0001",
                "stop_reason": "MT",
                "stop_reason_description": "MANUTENCAO",
                "observation": "Troca de ferramenta",
                "hours": 0.5,
                "stop_cost": 120.0,
                "cost_source": "HH",
            },
            {
                "dataReferencia": "2026-09-16",
                "op": "10916601006",
                "operacao": "02",
                "recurso": "MAQ02",
                "nomeOperador": "MARIA",
                "motivo": "OT",
                "motivoDescricao": "OUTROS",
                "observacao": "",
                "tempoHoras": 0.25,
                "valorParada": 40.0,
            },
        ]
    )
    payload = _service(gateway).list_for_work_center(
        token=_token(),
        branch="01",
        work_center="CT-01A",
    )

    assert payload["work_center"] == "CT-01A"
    assert payload["period"] == {"start_date": "2026-09-16", "end_date": "2026-09-16"}
    assert payload["shift"]["id"] == "2"
    assert payload["summary"]["appointment_count"] == 2
    assert payload["summary"]["total_hours"] == 0.75
    assert gateway.calls[0]["shift"] == "2"
    assert gateway.calls[0]["resource"] == "MAQ01,MAQ02"
    assert gateway.calls[0]["start_date"] == "2026-09-16"

    first = payload["items"][0]
    assert first["stop_reason"] == "MT"
    assert first["stop_reason_description"] == "MANUTENCAO"
    assert first["observation"] == "Troca de ferramenta"
    assert first["hours"] == 0.5
    assert first["operator_name"] == "JOAO"
    assert "stop_cost" not in first
    assert "operator_code" not in first

    second = payload["items"][1]
    assert second["stop_reason"] == "OT"
    assert second["observation"] is None


def test_rejects_work_center_outside_published_queue() -> None:
    with pytest.raises(ValueError, match="não está na fila"):
        _service(FakeGateway(), machine_load=FakeMachineLoad(None)).list_for_work_center(
            token=_token(),
            branch="01",
            work_center="CT-99",
        )


def test_rejects_invalid_token() -> None:
    with pytest.raises(PublicAccessDenied):
        _service(FakeGateway()).list_for_work_center(
            token="invalid",
            branch="01",
            work_center="CT-01A",
        )


def test_gateway_failure_surfaces_as_delpi_error() -> None:
    with pytest.raises(DelpiGatewayError):
        _service(FakeGateway(fail=True)).list_for_work_center(
            token=_token(),
            branch="01",
            work_center="CT-01A",
        )

"""Unit — inspeções de processo públicas da OP+operação."""

from __future__ import annotations

from typing import Any

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_operation_process_inspections_service import (
    PublicOperationProcessInspectionsService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.rows = rows or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def fetch_process_inspections_for_operation(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise DelpiGatewayError("api-delpi fora.")
        return {
            "success": True,
            "data": {
                "items": self.rows,
                "summary": {"inspection_count": len(self.rows)},
            },
        }


class FakeMachineLoad:
    def __init__(self, *, contains: bool = True) -> None:
        self.contains = contains

    def public_snapshot_contains_operation(self, **kwargs: Any) -> bool:
        return self.contains


def _service(
    gateway: FakeGateway,
    *,
    machine_load: FakeMachineLoad | None = None,
) -> PublicOperationProcessInspectionsService:
    return PublicOperationProcessInspectionsService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def test_lists_inspections_for_operation() -> None:
    gateway = FakeGateway(
        [
            {
                "inspector_name": "JOAO",
                "measurement_date": "2026-09-10",
                "measurement_time": "08:15",
                "result": "APROVADO",
                "result_code": "A",
            }
        ]
    )
    payload = _service(gateway).list_for_operation(
        token=_token(),
        branch="01",
        production_order="10964501004",
        operation_code="01",
    )
    assert gateway.calls[0]["production_order"] == "10964501004"
    assert gateway.calls[0]["operation"] == "01"
    assert payload["summary"]["inspection_count"] == 1
    assert payload["items"][0]["inspector_name"] == "JOAO"
    assert payload["items"][0]["result"] == "APROVADO"


def test_empty_when_no_inspections() -> None:
    payload = _service(FakeGateway([])).list_for_operation(
        token=_token(),
        branch="01",
        production_order="10964501004",
        operation_code="99",
    )
    assert payload["items"] == []
    assert payload["summary"]["inspection_count"] == 0


def test_rejects_invalid_token() -> None:
    with pytest.raises(PublicAccessDenied):
        _service(FakeGateway()).list_for_operation(
            token="invalido",
            branch="01",
            production_order="10964501004",
            operation_code="01",
        )


def test_rejects_operation_outside_published_queue() -> None:
    with pytest.raises(ValueError, match="fila publicada"):
        _service(FakeGateway(), machine_load=FakeMachineLoad(contains=False)).list_for_operation(
            token=_token(),
            branch="01",
            production_order="10964501004",
            operation_code="01",
        )


def test_propagates_gateway_failure() -> None:
    with pytest.raises(DelpiGatewayError):
        _service(FakeGateway(fail=True)).list_for_operation(
            token=_token(),
            branch="01",
            production_order="10964501004",
            operation_code="01",
        )

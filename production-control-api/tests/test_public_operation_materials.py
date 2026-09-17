"""Unit — materiais SD4 públicos da OP+operação."""

from __future__ import annotations

from typing import Any

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_operation_materials_service import (
    PublicOperationMaterialsService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService


class FakeGateway:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.rows = rows or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def fetch_production_order_operation_materials(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise DelpiGatewayError("api-delpi fora.")
        return {
            "success": True,
            "data": {
                "items": self.rows,
                "summary": {"material_count": len(self.rows)},
            },
        }


class FakeMachineLoad:
    def __init__(self, *, contains: bool = True) -> None:
        self.contains = contains
        self.calls: list[dict[str, Any]] = []

    def public_snapshot_contains_operation(self, **kwargs: Any) -> bool:
        self.calls.append(kwargs)
        return self.contains


def _service(
    gateway: FakeGateway,
    *,
    machine_load: FakeMachineLoad | None = None,
) -> PublicOperationMaterialsService:
    return PublicOperationMaterialsService(
        gateway,
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def test_lists_materials_for_operation() -> None:
    gateway = FakeGateway(
        [
            {
                "product_code": "10080001",
                "description": "Terminal",
                "unit": "PC",
                "original_qty": 10.0,
                "open_qty": 4.0,
                "consumed_qty": 6.0,
                "commitment_count": 2,
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
    assert gateway.calls[0]["branch"] == "01"
    assert payload["summary"]["material_count"] == 1
    assert payload["summary"]["commitment_count"] == 2
    assert payload["items"][0]["product_code"] == "10080001"
    assert payload["items"][0]["original_qty"] == 10.0
    assert payload["items"][0]["open_qty"] == 4.0
    assert payload["items"][0]["consumed_qty"] == 6.0


def test_empty_materials_when_operation_has_no_link() -> None:
    payload = _service(FakeGateway([])).list_for_operation(
        token=_token(),
        branch="01",
        production_order="10964501004",
        operation_code="99",
    )
    assert payload["items"] == []
    assert payload["summary"]["material_count"] == 0


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

"""Cockpit do alimentador — corte, rateio, degradação, lista de coleta e RBAC."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.line_feeder_service import LineFeederService
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    SnapshotNotFound,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

FULL_PERMS = (
    "production-control.access",
    "production-control.line-feeder.view",
    "production-control.view.filial-01",
)


def _user(*permissions: str):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=list(permissions),
        id="user-1",
        email="alimentador@delpi.com.br",
    )


def _operation(
    *,
    work_center: str,
    order: str,
    operation: str = "01",
    scheduled_date: str | None = "2026-09-22",
    scheduled_time: str | None = "08:00",
) -> dict[str, Any]:
    return {
        "work_center": work_center,
        "work_center_name": f"BANCADA {work_center}",
        "production_order": order,
        "operation_code": operation,
        "scheduled_date": scheduled_date,
        "scheduled_start_time": scheduled_time,
    }


def _commitment(
    order: str,
    product: str,
    qty: float,
    *,
    operation: str = "01",
    product_type: str = "MP",
) -> dict[str, Any]:
    return {
        "production_order": order,
        "operation": operation,
        "product_code": product,
        "description": f"MATERIAL {product}",
        "unit": "PC",
        "product_type": product_type,
        "original_qty": qty,
        "open_qty": qty,
        "consumed_qty": 0.0,
        "commitment_count": 1,
    }


class FakeSnapshots:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        if payload is not None:
            self.put("01", payload)

    def put(self, branch: str, payload: dict[str, Any]) -> None:
        self.rows[branch] = {
            "id": "snap-1",
            "branch": branch,
            "start_date": date(2026, 9, 22),
            "end_date": date(2026, 9, 26),
            "payload_json": payload,
            "refreshed_at": datetime(2026, 9, 22, 6, 0, tzinfo=timezone.utc),
        }

    def get(self, *, branch: str) -> dict[str, Any] | None:
        return self.rows.get(branch)


class FakeGateway:
    def __init__(
        self,
        *,
        commitments: list[dict[str, Any]] | None = None,
        balances: dict[str, dict[str, float]] | None = None,
        balances_fail: bool = False,
        locations: dict[str, str] | None = None,
        locations_fail: bool = False,
    ) -> None:
        self.commitments = commitments or []
        self.balances = balances or {}
        self.balances_fail = balances_fail
        self.locations = locations or {}
        self.locations_fail = locations_fail
        self.batch_calls: list[dict[str, Any]] = []
        self.balance_calls: list[dict[str, Any]] = []
        self.location_calls: list[dict[str, Any]] = []

    def fetch_operation_materials_batch(
        self,
        *,
        branch: str,
        production_orders: list[str],
    ) -> dict[str, Any]:
        self.batch_calls.append({"branch": branch, "production_orders": list(production_orders)})
        wanted = set(production_orders)
        return {
            "success": True,
            "data": {
                "items": [
                    row for row in self.commitments if row["production_order"] in wanted
                ]
            },
        }

    def fetch_product_physical_locations(
        self,
        *,
        branch: str,
        product_codes: list[str],
    ) -> dict[str, Any]:
        if self.locations_fail:
            raise DelpiGatewayError("api-delpi indisponível.")
        self.location_calls.append(
            {"branch": branch, "product_codes": list(product_codes)}
        )
        wanted = set(product_codes or [])
        rows = [
            {"product_code": code, "physical_location": location}
            for code, location in self.locations.items()
            if not wanted or code in wanted
        ]
        return {"success": True, "data": {"items": rows}}

    def fetch_stock_balances_items(
        self,
        *,
        branch: str,
        warehouse: str,
        only_positive: bool = True,
        page: int = 1,
        page_size: int = 500,
        sort: str = "product_code_asc",
        product_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.balances_fail:
            raise DelpiGatewayError("api-delpi indisponível.")
        self.balance_calls.append(
            {
                "branch": branch,
                "warehouse": warehouse,
                "only_positive": only_positive,
                "page": page,
                "product_codes": list(product_codes or []),
            }
        )
        wanted = set(product_codes or [])
        rows = [
            {"product_code": code, "quantity": qty, "warehouse": warehouse}
            for code, qty in (self.balances.get(warehouse) or {}).items()
            if not wanted or code in wanted
        ]
        return {"success": True, "data": {"items": rows}}


class FakePickPlans:
    def __init__(self) -> None:
        self.plans: dict[str, dict[str, Any]] = {}
        self.items: dict[str, list[dict[str, Any]]] = {}

    def create_plan(
        self,
        *,
        branch: str,
        cutoff_at: datetime,
        work_center: str | None,
        created_by: str | None,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        plan_id = str(uuid4())
        plan = {
            "id": plan_id,
            "branch": branch,
            "cutoff_at": cutoff_at,
            "work_center": work_center,
            "status": "open",
            "created_at": datetime(2026, 9, 22, 7, 0, tzinfo=timezone.utc),
            "created_by": created_by,
            "updated_at": datetime(2026, 9, 22, 7, 0, tzinfo=timezone.utc),
            "updated_by": created_by,
        }
        self.plans[plan_id] = plan
        self.items[plan_id] = [
            {
                **item,
                "id": str(uuid4()),
                "plan_id": plan_id,
                "status": "pending",
                "updated_at": datetime(2026, 9, 22, 7, 0, tzinfo=timezone.utc),
                "updated_by": created_by,
            }
            for item in items
        ]
        return {**plan, "items": list(self.items[plan_id])}

    def get_plan(self, *, plan_id: str, branch: str) -> dict[str, Any] | None:
        plan = self.plans.get(plan_id)
        if plan is None or plan["branch"] != branch:
            return None
        return {**plan, "items": list(self.items.get(plan_id) or [])}

    def list_plans(
        self,
        *,
        branch: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = []
        for plan in self.plans.values():
            if plan["branch"] != branch:
                continue
            if status and plan["status"] != status:
                continue
            items = self.items.get(plan["id"]) or []
            rows.append(
                {
                    **plan,
                    "item_count": len(items),
                    "pending_count": sum(1 for i in items if i["status"] == "pending"),
                    "picked_count": sum(1 for i in items if i["status"] == "picked"),
                    "delivered_count": sum(1 for i in items if i["status"] == "delivered"),
                    "to_deliver_qty": sum(float(i["to_deliver_qty"]) for i in items),
                }
            )
        return rows[:limit]

    def update_item_status(
        self,
        *,
        plan_id: str,
        item_id: str,
        branch: str,
        status: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        plan = self.plans.get(plan_id)
        if plan is None or plan["branch"] != branch:
            return None
        for item in self.items.get(plan_id) or []:
            if item["id"] == item_id:
                item["status"] = status
                item["updated_by"] = updated_by
                return dict(item)
        return None

    def close_plan(
        self,
        *,
        plan_id: str,
        branch: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        plan = self.plans.get(plan_id)
        if plan is None or plan["branch"] != branch:
            return None
        plan["status"] = "closed"
        plan["updated_by"] = updated_by
        items = self.items.get(plan_id) or []
        return {
            **plan,
            "item_count": len(items),
            "pending_count": sum(1 for i in items if i["status"] == "pending"),
            "picked_count": sum(1 for i in items if i["status"] == "picked"),
            "delivered_count": sum(1 for i in items if i["status"] == "delivered"),
            "to_deliver_qty": sum(float(i["to_deliver_qty"]) for i in items),
        }


def _payload(operations: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    centers: list[dict[str, Any]] = []
    for item in operations:
        code = item["work_center"]
        if not any(center["work_center"] == code for center in centers):
            centers.append({"work_center": code, "work_center_name": item["work_center_name"]})
    return {"work_centers": centers, "operations": operations, **extra}


def _service(
    *,
    operations: list[dict[str, Any]] | None = None,
    commitments: list[dict[str, Any]] | None = None,
    balances: dict[str, dict[str, float]] | None = None,
    balances_fail: bool = False,
    locations: dict[str, str] | None = None,
    locations_fail: bool = False,
    payload: dict[str, Any] | None = None,
    pick_plans: FakePickPlans | None = None,
) -> tuple[LineFeederService, FakeGateway, FakePickPlans]:
    snapshot_payload = payload if payload is not None else _payload(operations or [])
    gateway = FakeGateway(
        commitments=commitments,
        balances=balances,
        balances_fail=balances_fail,
        locations=locations,
        locations_fail=locations_fail,
    )
    plans = pick_plans or FakePickPlans()
    # Cache próprio por teste: um teste não pode herdar o cálculo de outro.
    from production_control_app.application.services.line_feeder_service import (
        _RequirementsCache,
    )

    service = LineFeederService(
        gateway,
        snapshots=FakeSnapshots(snapshot_payload),
        pick_plans=plans,
        branch_access=BranchAccessService(),
        cache=_RequirementsCache(0),
    )
    return service, gateway, plans


def _requirements(service: LineFeederService, **kwargs: Any) -> dict[str, Any]:
    params = {
        "branch": "01",
        "cutoff_date": "2026-09-22",
        "cutoff_time": "14:00",
        **kwargs,
    }
    return service.get_requirements(_user(*FULL_PERMS), **params)


# --------------------------------------------------------------------------- #
# Necessidade: positivo, irmão e negativo
# --------------------------------------------------------------------------- #


def test_requirements_include_operation_before_cutoff() -> None:
    service, gateway, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001", scheduled_time="08:00")],
        commitments=[_commitment("10840401001", "50320064", 10.0)],
        balances={"99": {"50320064": 4.0}, "01": {"50320064": 100.0}},
    )
    data = _requirements(service)

    assert data["branch"] == "01"
    assert data["cutoff"] == {
        "at": "2026-09-22T14:00:00",
        "date": "2026-09-22",
        "time": "14:00",
    }
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["work_center"] == "CT-01"
    assert item["product_code"] == "50320064"
    assert item["required_qty"] == 10.0
    assert item["point_of_use_qty"] == 4.0
    assert item["to_deliver_qty"] == 6.0
    assert item["status"] == "to_pick"
    assert item["first_production_order"] == "10840401001"
    assert data["summary"]["to_deliver_qty"] == 6.0
    assert data["stock"] == {
        "available": True,
        "point_of_use_warehouse": "99",
        "source_warehouse": "01",
    }
    # Um lote de empenhos e um saldo por armazém — não uma chamada por operação.
    assert len(gateway.batch_calls) == 1
    assert [call["warehouse"] for call in gateway.balance_calls] == ["99", "01"]
    assert gateway.balance_calls[0]["only_positive"] is False
    assert gateway.balance_calls[0]["product_codes"] == ["50320064"]


def test_requirements_include_sibling_work_center_in_same_cutoff() -> None:
    service, _, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-02", order="10840402001", scheduled_time="13:30"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 5.0),
            _commitment("10840402001", "50320099", 7.0),
        ],
        balances={"99": {}, "01": {"50320064": 100.0, "50320099": 100.0}},
    )
    data = _requirements(service)

    assert {item["work_center"] for item in data["items"]} == {"CT-01", "CT-02"}
    assert [group["work_center"] for group in data["groups"]] == ["CT-01", "CT-02"]
    assert data["summary"]["work_center_count"] == 2
    assert [center["work_center"] for center in data["work_centers"]] == ["CT-01", "CT-02"]


def test_requirements_exclude_operation_after_cutoff() -> None:
    service, gateway, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-01", order="10840401002", scheduled_time="16:00"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 5.0),
            _commitment("10840401002", "50320099", 5.0),
        ],
        balances={"99": {}, "01": {"50320064": 100.0, "50320099": 100.0}},
    )
    data = _requirements(service)

    assert [item["product_code"] for item in data["items"]] == ["50320064"]
    # A OP de depois do corte não deve nem ser consultada na api-delpi.
    assert gateway.batch_calls[0]["production_orders"] == ["10840401001"]


def test_requirements_exclude_withdrawn_conjunto() -> None:
    operations = [
        _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
        _operation(work_center="CT-01", order="10840501001", scheduled_time="09:00"),
    ]
    payload = _payload(
        operations,
        withdrawn_conjuntos=[{"order_number": "108405", "operation_count": 1}],
    )
    service, _, _ = _service(
        payload=payload,
        commitments=[
            _commitment("10840401001", "50320064", 5.0),
            _commitment("10840501001", "50320099", 5.0),
        ],
        balances={"99": {}, "01": {"50320064": 100.0, "50320099": 100.0}},
    )
    data = _requirements(service)

    assert [item["product_code"] for item in data["items"]] == ["50320064"]


def test_requirements_without_snapshot_raise_not_found() -> None:
    service, _, _ = _service(operations=[])
    service._snapshots.rows.clear()  # type: ignore[attr-defined]
    with pytest.raises(SnapshotNotFound):
        _requirements(service)


def test_requirements_reject_missing_and_malformed_cutoff() -> None:
    service, _, _ = _service(operations=[])
    with pytest.raises(ValueError):
        _requirements(service, cutoff_date=None)
    with pytest.raises(ValueError):
        _requirements(service, cutoff_time="25:00")


def test_requirements_reject_unknown_status_filter() -> None:
    service, _, _ = _service(operations=[])
    with pytest.raises(ValueError):
        _requirements(service, status="banana")


# --------------------------------------------------------------------------- #
# Rateio no serviço: o filtro de bancada não pode mudar a conta
# --------------------------------------------------------------------------- #


def _shared_stock_service() -> LineFeederService:
    service, _, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-02", order="10840402001", scheduled_time="13:00"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 10.0),
            _commitment("10840402001", "50320064", 10.0),
        ],
        balances={"99": {"50320064": 10.0}, "01": {"50320064": 4.0}},
    )
    return service


def test_shared_material_is_allocated_fifo_between_work_centers() -> None:
    data = _requirements(_shared_stock_service())
    by_center = {item["work_center"]: item for item in data["items"]}

    assert by_center["CT-01"]["to_deliver_qty"] == 0.0
    assert by_center["CT-01"]["status"] == "covered"
    assert by_center["CT-02"]["to_deliver_qty"] == 10.0
    assert by_center["CT-02"]["source_available_qty"] == 4.0
    assert by_center["CT-02"]["status"] == "at_risk"
    # A bancada em risco lidera a leitura.
    assert data["groups"][0]["work_center"] == "CT-02"


def test_work_center_filter_does_not_change_allocation() -> None:
    """Filtrar a tela não pode transformar «em risco» em «coberto»."""
    filtered = _requirements(_shared_stock_service(), work_center="CT-02")

    assert [item["work_center"] for item in filtered["items"]] == ["CT-02"]
    assert filtered["items"][0]["to_deliver_qty"] == 10.0
    assert filtered["items"][0]["status"] == "at_risk"
    assert filtered["filters"]["work_center"] == "CT-02"
    # O catálogo de bancadas continua completo para não prender o usuário no filtro.
    assert [center["work_center"] for center in filtered["work_centers"]] == ["CT-01", "CT-02"]


def test_status_filter_keeps_only_requested_status() -> None:
    data = _requirements(_shared_stock_service(), status="at_risk")
    assert [item["status"] for item in data["items"]] == ["at_risk"]
    assert data["summary"]["covered_count"] == 0


# --------------------------------------------------------------------------- #
# Degradação por bloco
# --------------------------------------------------------------------------- #


def test_balances_failure_keeps_requirements_and_flags_stock_unavailable() -> None:
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 10.0)],
        balances_fail=True,
    )
    data = _requirements(service)

    assert data["stock"]["available"] is False
    assert data["stock"]["message"]
    item = data["items"][0]
    assert item["required_qty"] == 10.0
    assert item["to_deliver_qty"] is None
    assert item["status"] == "unknown"
    assert data["summary"]["unknown_count"] == 1


def test_commitments_failure_is_not_degraded() -> None:
    """Sem empenho não existe necessidade: a tela deve falhar, não mentir zero."""
    service, gateway, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
    )

    def boom(**_kwargs: Any) -> dict[str, Any]:
        raise DelpiGatewayError("api-delpi indisponível.")

    gateway.fetch_operation_materials_batch = boom  # type: ignore[assignment]
    with pytest.raises(DelpiGatewayError):
        _requirements(service)


def _settings_override(**overrides: int):
    def setting_int(key: str, default: int) -> int:
        return overrides.get(key, default)

    return setting_int


def _four_order_service(**kwargs: Any):
    return _service(
        operations=[
            _operation(work_center="CT-01", order=f"1084040100{index}", scheduled_time="08:00")
            for index in range(1, 5)
        ],
        commitments=[
            _commitment(f"1084040100{index}", f"5032006{index}", 1.0) for index in range(1, 5)
        ],
        balances={"99": {}, "01": {}},
        **kwargs,
    )


def test_batch_slices_orders_into_chunks_without_losing_need(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O teto por requisição é contrato da api-delpi: o corte inteiro é fatiado.

    Um corte real da filial passa de 500 OPs; truncar por requisição esconderia
    metade do que a bancada precisa.
    """
    from production_control_app.application.services import line_feeder_service as module

    monkeypatch.setattr(module, "setting_int", _settings_override(commitmentBatchSize=2))
    service, gateway, _ = _four_order_service()
    data = _requirements(service)

    assert sorted(call["production_orders"] for call in gateway.batch_calls) == [
        ["10840401001", "10840401002"],
        ["10840401003", "10840401004"],
    ]
    assert data["stock"].get("truncated_orders") is None
    assert data["summary"]["production_order_count"] == 4
    assert {item["product_code"] for item in data["items"]} == {
        "50320061",
        "50320062",
        "50320063",
        "50320064",
    }


def test_batch_flags_truncation_only_above_the_batch_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from production_control_app.application.services import line_feeder_service as module

    monkeypatch.setattr(
        module,
        "setting_int",
        _settings_override(commitmentBatchSize=2, maxCommitmentBatches=1),
    )
    service, gateway, _ = _four_order_service()
    data = _requirements(service)

    assert [call["production_orders"] for call in gateway.batch_calls] == [
        ["10840401001", "10840401002"],
    ]
    assert data["stock"]["truncated_orders"] is True


def test_parallel_reads_keep_the_caller_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """O gateway lê o JWT de contextvars, que não é herdado por thread.

    Sem propagar o contexto, a mesma rota trocaria a identidade do usuário pelo
    token de serviço só porque o corte ficou grande o bastante para fatiar.
    """
    from contextvars import ContextVar

    from production_control_app.application.services import line_feeder_service as module

    caller: ContextVar[str] = ContextVar("caller")
    caller.set("alimentador@delpi.com.br")
    seen: list[str] = []

    monkeypatch.setattr(module, "setting_int", _settings_override(commitmentBatchSize=2))
    service, gateway, _ = _four_order_service()
    original = gateway.fetch_operation_materials_batch

    def spy(**kwargs: Any) -> dict[str, Any]:
        seen.append(caller.get("SEM_IDENTIDADE"))
        return original(**kwargs)

    gateway.fetch_operation_materials_batch = spy  # type: ignore[assignment]
    _requirements(service)

    assert len(seen) == 2
    assert set(seen) == {"alimentador@delpi.com.br"}


def test_commitment_batch_never_exceeds_the_api_delpi_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O lote configurado nunca passa do teto por requisição do contrato."""
    from production_control_app.application.services import line_feeder_service as module

    monkeypatch.setattr(
        module,
        "setting_int",
        _settings_override(commitmentBatchSize=500, maxProductionOrdersPerBatch=3),
    )
    service, gateway, _ = _four_order_service()
    _requirements(service)

    assert [len(call["production_orders"]) for call in gateway.batch_calls] == [3, 1]


# --------------------------------------------------------------------------- #
# Lista de coleta
# --------------------------------------------------------------------------- #


def _plan_service() -> tuple[LineFeederService, FakePickPlans]:
    service, _, plans = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-02", order="10840402001", scheduled_time="09:00"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 10.0),
            _commitment("10840402001", "50320099", 6.0),
        ],
        # 50320099 já está inteiro na bancada: não pode entrar na coleta.
        balances={"99": {"50320099": 6.0}, "01": {"50320064": 100.0}},
        locations={"50320064": "A-01", "50320099": "B-02"},
    )
    return service, plans


def test_pick_plan_only_persists_what_is_missing_at_the_bench() -> None:
    service, _ = _plan_service()
    created = service.create_pick_plan(
        _user(*FULL_PERMS),
        branch="01",
        cutoff_date="2026-09-22",
        cutoff_time="14:00",
    )

    assert created["plan"]["status"] == "open"
    assert created["plan"]["item_count"] == 1
    assert created["plan"]["pending_count"] == 1
    assert created["plan"]["to_deliver_qty"] == 10.0
    item = created["items"][0]
    assert item["product_code"] == "50320064"
    assert item["pickup_location"] == "A-01"
    assert "work_center" not in item
    assert "production_order" not in item
    assert item["status"] == "pending"


def test_pick_plan_collapses_same_product_across_benches() -> None:
    service, _, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-02", order="10840402001", scheduled_time="09:00"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 4.0),
            _commitment("10840402001", "50320064", 6.0),
        ],
        balances={"99": {}, "01": {"50320064": 100.0}},
        locations={"50320064": "A-01"},
    )
    created = service.create_pick_plan(
        _user(*FULL_PERMS),
        branch="01",
        cutoff_date="2026-09-22",
        cutoff_time="14:00",
    )
    assert len(created["items"]) == 1
    assert created["items"][0]["product_code"] == "50320064"
    assert created["items"][0]["to_deliver_qty"] == 10.0
    assert created["items"][0]["pickup_location"] == "A-01"


def test_pick_plan_sorted_by_product_code() -> None:
    service, _, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-01", order="10840401002", scheduled_time="09:00"),
        ],
        commitments=[
            _commitment("10840401001", "90320064", 1.0),
            _commitment("10840401002", "50320064", 1.0),
        ],
        balances={"99": {}, "01": {"50320064": 10.0, "90320064": 10.0}},
    )
    created = service.create_pick_plan(
        _user(*FULL_PERMS),
        branch="01",
        cutoff_date="2026-09-22",
        cutoff_time="14:00",
    )
    assert [item["product_code"] for item in created["items"]] == [
        "50320064",
        "90320064",
    ]


def test_requirements_include_pickup_location() -> None:
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 10.0)],
        balances={"99": {}, "01": {"50320064": 10.0}},
        locations={"50320064": "A-01"},
    )
    data = _requirements(service)
    assert data["items"][0]["pickup_location"] == "A-01"


def test_pickup_location_failure_does_not_block_requirements() -> None:
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 10.0)],
        balances={"99": {}, "01": {"50320064": 10.0}},
        locations_fail=True,
    )
    data = _requirements(service)
    assert data["items"][0]["pickup_location"] == ""


def test_pick_plan_for_single_work_center_ignores_other_benches() -> None:
    service, _, _ = _service(
        operations=[
            _operation(work_center="CT-01", order="10840401001", scheduled_time="08:00"),
            _operation(work_center="CT-02", order="10840402001", scheduled_time="09:00"),
        ],
        commitments=[
            _commitment("10840401001", "50320064", 10.0),
            _commitment("10840402001", "50320099", 6.0),
        ],
        balances={"99": {}, "01": {"50320064": 100.0, "50320099": 100.0}},
    )
    created = service.create_pick_plan(
        _user(*FULL_PERMS),
        branch="01",
        cutoff_date="2026-09-22",
        cutoff_time="14:00",
        work_center="CT-02",
    )
    assert created["plan"]["work_center"] == "CT-02"
    assert [item["product_code"] for item in created["items"]] == ["50320099"]


def test_pick_plan_for_covered_work_center_is_refused() -> None:
    """Lista vazia não vira registro: o alimentador não tem nada para fazer nela."""
    service, _ = _plan_service()
    with pytest.raises(ValueError):
        service.create_pick_plan(
            _user(*FULL_PERMS),
            branch="01",
            cutoff_date="2026-09-22",
            cutoff_time="14:00",
            work_center="CT-02",
        )


def test_pick_plan_refuses_when_nothing_is_missing() -> None:
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 5.0)],
        balances={"99": {"50320064": 5.0}, "01": {}},
    )
    with pytest.raises(ValueError):
        service.create_pick_plan(
            _user(*FULL_PERMS),
            branch="01",
            cutoff_date="2026-09-22",
            cutoff_time="14:00",
        )


def test_pick_plan_refuses_when_stock_is_unknown() -> None:
    """Sem saldo medido, a lista mandaria buscar o que já está na bancada."""
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 5.0)],
        balances_fail=True,
    )
    with pytest.raises(DelpiGatewayError):
        service.create_pick_plan(
            _user(*FULL_PERMS),
            branch="01",
            cutoff_date="2026-09-22",
            cutoff_time="14:00",
        )


def test_pick_item_status_moves_forward_and_back() -> None:
    service, _ = _plan_service()
    user = _user(*FULL_PERMS)
    created = service.create_pick_plan(
        user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    plan_id = created["plan"]["id"]
    item_id = created["items"][0]["id"]

    picked = service.update_pick_item_status(
        user, branch="01", plan_id=plan_id, item_id=item_id, status="picked"
    )
    assert picked["item"]["status"] == "picked"
    assert picked["item"]["updated_by"] == "alimentador@delpi.com.br"

    delivered = service.update_pick_item_status(
        user, branch="01", plan_id=plan_id, item_id=item_id, status="delivered"
    )
    assert delivered["item"]["status"] == "delivered"

    # Reversão existe: o alimentador erra o toque no chão de fábrica.
    back = service.update_pick_item_status(
        user, branch="01", plan_id=plan_id, item_id=item_id, status="pending"
    )
    assert back["item"]["status"] == "pending"

    detail = service.get_pick_plan(user, branch="01", plan_id=plan_id)
    assert detail["plan"]["pending_count"] == 1
    assert detail["plan"]["delivered_count"] == 0


def test_pick_item_status_rejects_unknown_status() -> None:
    service, _ = _plan_service()
    user = _user(*FULL_PERMS)
    created = service.create_pick_plan(
        user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    with pytest.raises(ValueError):
        service.update_pick_item_status(
            user,
            branch="01",
            plan_id=created["plan"]["id"],
            item_id=created["items"][0]["id"],
            status="lost",
        )


def test_closed_plan_does_not_accept_item_changes() -> None:
    service, _ = _plan_service()
    user = _user(*FULL_PERMS)
    created = service.create_pick_plan(
        user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    plan_id = created["plan"]["id"]
    closed = service.close_pick_plan(user, branch="01", plan_id=plan_id)
    assert closed["plan"]["status"] == "closed"

    with pytest.raises(ValueError):
        service.update_pick_item_status(
            user,
            branch="01",
            plan_id=plan_id,
            item_id=created["items"][0]["id"],
            status="picked",
        )


def test_plan_from_another_branch_is_not_readable() -> None:
    service, _ = _plan_service()
    user = _user(*FULL_PERMS, "production-control.view.filial-02")
    created = service.create_pick_plan(
        user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    with pytest.raises(LookupError):
        service.get_pick_plan(user, branch="02", plan_id=created["plan"]["id"])


def test_plan_id_must_be_an_identifier() -> None:
    service, _ = _plan_service()
    with pytest.raises(ValueError):
        service.get_pick_plan(_user(*FULL_PERMS), branch="01", plan_id="nope")


def test_list_plans_filters_by_status() -> None:
    service, _ = _plan_service()
    user = _user(*FULL_PERMS)
    created = service.create_pick_plan(
        user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    service.close_pick_plan(user, branch="01", plan_id=created["plan"]["id"])

    open_plans = service.list_pick_plans(user, branch="01", status="open")
    closed_plans = service.list_pick_plans(user, branch="01", status="closed")
    assert open_plans["items"] == []
    assert len(closed_plans["items"]) == 1
    assert closed_plans["items"][0]["item_count"] == 1

    with pytest.raises(ValueError):
        service.list_pick_plans(user, branch="01", status="banana")


# --------------------------------------------------------------------------- #
# RBAC — os dois gates
# --------------------------------------------------------------------------- #


def test_requires_line_feeder_permission() -> None:
    service, _, _ = _service(operations=[])
    user = _user("production-control.access", "production-control.view.filial-01")
    with pytest.raises(PermissionError):
        service.get_requirements(
            user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
        )


def test_requires_branch_permission() -> None:
    service, _, _ = _service(operations=[])
    user = _user("production-control.access", "production-control.line-feeder.view")
    with pytest.raises(BranchAccessDenied):
        service.get_requirements(
            user, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
        )


def test_rejects_invalid_branch() -> None:
    service, _, _ = _service(operations=[])
    with pytest.raises(InvalidBranch):
        service.get_requirements(
            _user(*FULL_PERMS), branch="09", cutoff_date="2026-09-22", cutoff_time="14:00"
        )


def test_write_actions_require_the_same_permission() -> None:
    """A permissão de leitura governa a coleta — mas quem não a tem não escreve."""
    service, plans = _plan_service()
    created = service.create_pick_plan(
        _user(*FULL_PERMS), branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
    )
    outsider = _user("production-control.access", "production-control.view.filial-01")
    for action in (
        lambda: service.create_pick_plan(
            outsider, branch="01", cutoff_date="2026-09-22", cutoff_time="14:00"
        ),
        lambda: service.update_pick_item_status(
            outsider,
            branch="01",
            plan_id=created["plan"]["id"],
            item_id=created["items"][0]["id"],
            status="picked",
        ),
        lambda: service.close_pick_plan(
            outsider, branch="01", plan_id=created["plan"]["id"]
        ),
    ):
        with pytest.raises(PermissionError):
            action()
    assert plans.items[created["plan"]["id"]][0]["status"] == "pending"


# --------------------------------------------------------------------------- #
# Contrato HTTP
# --------------------------------------------------------------------------- #


def _client(service: LineFeederService, *, permissions: tuple[str, ...] = FULL_PERMS) -> TestClient:
    from production_control_app.interface.http.routes import line_feeder_routes

    line_feeder_routes.build_line_feeder_service = lambda: service  # type: ignore[assignment]
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = _user(*permissions)
        return await call_next(request)

    app.include_router(line_feeder_routes.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_line_feeder_routes():
    from production_control_app.interface.http.routes import line_feeder_routes

    original = line_feeder_routes.build_line_feeder_service
    yield
    line_feeder_routes.build_line_feeder_service = original  # type: ignore[assignment]


def test_route_returns_requirements_envelope() -> None:
    service, _, _ = _service(
        operations=[_operation(work_center="CT-01", order="10840401001")],
        commitments=[_commitment("10840401001", "50320064", 10.0)],
        balances={"99": {}, "01": {"50320064": 100.0}},
    )
    response = _client(service).get(
        "/line-feeder/requirements",
        params={"branch": "01", "cutoffDate": "2026-09-22", "cutoffTime": "14:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"][0]["to_deliver_qty"] == 10.0
    assert body["data"]["statuses"]["to_pick"]["label"]


def test_route_requires_cutoff_date() -> None:
    service, _, _ = _service(operations=[])
    response = _client(service).get("/line-feeder/requirements", params={"branch": "01"})
    assert response.status_code == 422


def test_route_maps_permission_denied_to_403() -> None:
    service, _, _ = _service(operations=[])
    response = _client(
        service,
        permissions=("production-control.access", "production-control.view.filial-01"),
    ).get(
        "/line-feeder/requirements",
        params={"branch": "01", "cutoffDate": "2026-09-22"},
    )
    assert response.status_code == 403
    assert response.json()["success"] is False


def test_route_maps_missing_snapshot_to_404() -> None:
    service, _, _ = _service(operations=[])
    service._snapshots.rows.clear()  # type: ignore[attr-defined]
    response = _client(service).get(
        "/line-feeder/requirements",
        params={"branch": "01", "cutoffDate": "2026-09-22"},
    )
    assert response.status_code == 404


def test_route_pick_plan_lifecycle() -> None:
    service, _ = _plan_service()
    client = _client(service)

    created = client.post(
        "/line-feeder/pick-plans",
        json={"branch": "01", "cutoffDate": "2026-09-22", "cutoffTime": "14:00"},
    )
    assert created.status_code == 200
    plan = created.json()["data"]["plan"]
    item = created.json()["data"]["items"][0]

    listed = client.get("/line-feeder/pick-plans", params={"branch": "01"})
    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["id"] == plan["id"]

    detail = client.get(
        f"/line-feeder/pick-plans/{plan['id']}", params={"branch": "01"}
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["items"][0]["id"] == item["id"]

    patched = client.patch(
        f"/line-feeder/pick-plans/{plan['id']}/items/{item['id']}",
        json={"branch": "01", "status": "delivered"},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["item"]["status"] == "delivered"

    closed = client.post(
        f"/line-feeder/pick-plans/{plan['id']}/close", json={"branch": "01"}
    )
    assert closed.status_code == 200
    assert closed.json()["data"]["plan"]["status"] == "closed"


def test_route_unknown_plan_returns_404() -> None:
    service, _ = _plan_service()
    response = _client(service).get(
        f"/line-feeder/pick-plans/{uuid4()}", params={"branch": "01"}
    )
    assert response.status_code == 404


def test_route_invalid_plan_id_returns_422() -> None:
    service, _ = _plan_service()
    response = _client(service).get(
        "/line-feeder/pick-plans/not-a-uuid", params={"branch": "01"}
    )
    assert response.status_code == 422

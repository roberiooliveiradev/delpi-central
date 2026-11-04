"""Etapa 3 — necessidade dinâmica de materiais (saldo real do ponto de uso)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.line_feeder_service import LineFeederService
from production_control_app.domain.errors import DelpiGatewayError, HorizonPreviewStale
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.line_feeder_materials import (
    CoveredOperationDemand,
    apply_factory_stock,
    build_material_demands,
    commitment_material_qty,
    proportional_material_qty,
)
from production_control_app.domain.services.operation_materials_batch import (
    validated_operation_materials_batch_items,
)

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


# --------------------------------------------------------------------------- #
# Domínio puro
# --------------------------------------------------------------------------- #


def test_commitment_qty_is_full_open_even_when_partial_coverage() -> None:
    """AC-02: cobertura temporal parcial → demanda = empenho aberto integral."""
    assert commitment_material_qty(open_qty=Decimal("100")) == Decimal("100")
    # Compat wrapper não aplica mais proporção covered/pending.
    assert proportional_material_qty(
        open_qty=Decimal("100"),
        covered_qty=Decimal("40"),
        pending_qty=Decimal("100"),
    ) == Decimal("100")


def test_partial_coverage_uses_full_open_commitment() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP3",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("40"),
            pending_qty=Decimal("100"),
            pa_product_code="90262910",
        )
    ]
    commitments = {
        ("OP3", "1"): [
            {
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 100,
            }
        ]
    }
    buckets, _, ok = build_material_demands(ops, commitments)
    assert ok
    assert buckets[0].required_qty == Decimal("100")
    origin = buckets[0].origins[0]
    assert origin.required_qty == 100.0
    assert origin.open_qty == 100.0
    assert origin.fraction == 0.4
    assert origin.demand_basis == "open_commitment"
    assert origin.pa_product_code == "90262910"
    items = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 70},
        source_balances={"MP1": 1000},
        balances_available=True,
    )
    assert items[0]["required_qty"] == 100.0
    assert items[0]["to_collect_qty"] == 30.0
    assert items[0]["origins"][0]["pa_product_code"] == "90262910"


def test_stock_partial_and_repeat_same_result() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="01|CT-A|OP1|01",
            sequence_position=1,
            covered_qty=Decimal("100"),
            pending_qty=Decimal("100"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 100,
            }
        ]
    }
    buckets, _, ok = build_material_demands(ops, commitments)
    assert ok
    first = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 40},
        source_balances={"MP1": 1000},
        balances_available=True,
    )
    second = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 40},
        source_balances={"MP1": 1000},
        balances_available=True,
    )
    assert first[0]["to_collect_qty"] == 60.0
    assert second[0]["to_collect_qty"] == 60.0


def test_stock_updated_reduces_collect() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("100"),
            pending_qty=Decimal("100"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 100,
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    after = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 75},
        source_balances={},
        balances_available=True,
    )
    assert after[0]["to_collect_qty"] == 25.0


def test_shared_factory_stock_across_work_centers() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OPA",
            operation_code="01",
            operation_id="a",
            sequence_position=1,
            covered_qty=Decimal("60"),
            pending_qty=Decimal("60"),
        ),
        CoveredOperationDemand(
            work_center="CT-B",
            work_center_name="B",
            production_order="OPB",
            operation_code="01",
            operation_id="b",
            sequence_position=1,
            covered_qty=Decimal("50"),
            pending_qty=Decimal("50"),
        ),
    ]
    commitments = {
        ("OPA", "1"): [
            {
                "product_code": "MP1",
                "description": "Parafuso",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 60,
            }
        ],
        ("OPB", "1"): [
            {
                "product_code": "MP1",
                "description": "Parafuso",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 50,
            }
        ],
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    items = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 40},
        source_balances={"MP1": 200},
        balances_available=True,
    )
    assert len(items) == 1
    assert items[0]["required_qty"] == 110.0
    assert items[0]["factory_available_qty"] == 40.0
    assert items[0]["to_collect_qty"] == 70.0
    assert set(items[0]["work_centers"]) == {"CT-A", "CT-B"}


def test_substituted_commitment_replaces_old_material() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "NEW-MP",
                "description": "Novo",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 10,
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    assert [b.product_code for b in buckets] == ["NEW-MP"]


def test_non_mp_excluded_and_zero_open_ignored() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "PA1",
                "product_type": "PA",
                "open_qty": 10,
                "unit": "PC",
                "description": "PA",
            },
            {
                "product_code": "MP0",
                "product_type": "MP",
                "open_qty": 0,
                "unit": "PC",
                "description": "Zero",
            },
            {
                "product_code": "MP1",
                "product_type": "MP",
                "open_qty": 5,
                "unit": "PC",
                "description": "Ok",
            },
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    assert [b.product_code for b in buckets] == ["MP1"]
    assert buckets[0].required_qty == Decimal("5")


def test_sufficient_factory_stock_zero_collect() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "product_type": "MP",
                "open_qty": 10,
                "unit": "PC",
                "description": "Ok",
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    items = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 50},
        source_balances={},
        balances_available=True,
    )
    assert items[0]["to_collect_qty"] == 0.0
    assert items[0]["status"] == "covered"


def test_stock_unavailable_is_unknown_not_zero() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "product_type": "MP",
                "open_qty": 10,
                "unit": "PC",
                "description": "Ok",
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    items = apply_factory_stock(
        buckets,
        factory_balances=None,
        source_balances=None,
        balances_available=False,
    )
    assert items[0]["status"] == "unknown"
    assert items[0]["to_collect_qty"] is None
    assert items[0]["factory_available_qty"] is None


def test_source_warehouse_does_not_reduce_to_collect() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("100"),
            pending_qty=Decimal("100"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "product_type": "MP",
                "open_qty": 100,
                "unit": "PC",
                "description": "Ok",
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    items = apply_factory_stock(
        buckets,
        factory_balances={"MP1": 10},
        source_balances={"MP1": 9999},
        balances_available=True,
    )
    assert items[0]["to_collect_qty"] == 90.0
    assert items[0]["source_available_qty"] == 9999.0
    assert items[0]["status"] == "to_pick"


def test_negative_factory_stock_treated_as_zero() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    commitments = {
        ("OP1", "1"): [
            {
                "product_code": "MP1",
                "product_type": "MP",
                "open_qty": 10,
                "unit": "PC",
                "description": "Ok",
            }
        ]
    }
    buckets, _, _ = build_material_demands(ops, commitments)
    items = apply_factory_stock(
        buckets,
        factory_balances={"MP1": -5},
        source_balances={},
        balances_available=True,
    )
    assert items[0]["factory_available_qty"] == 0.0
    assert items[0]["to_collect_qty"] == 10.0


# --------------------------------------------------------------------------- #
# Serviço
# --------------------------------------------------------------------------- #


class FakePublications:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def put(self, branch: str, payload: dict[str, Any], *, row_version: str = "1") -> None:
        self.rows[branch] = {
            "branch": branch,
            "generation_id": "gen-1",
            "row_version": row_version,
            "start_date": date(2026, 9, 1),
            "end_date": date(2026, 9, 30),
            "payload_json": payload,
            "published_at": datetime(2026, 9, 20, tzinfo=timezone.utc),
            "published_by": "pcp",
            "source_refreshed_at": datetime(2026, 9, 19, tzinfo=timezone.utc),
        }

    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        return self.rows.get(branch)


class FakeSnapshots:
    def get(self, *, branch: str) -> dict[str, Any] | None:
        return None


class FakeGateway:
    def __init__(
        self,
        *,
        balances_ops: dict[tuple[str, str], dict[str, Any]],
        standard_times: dict[tuple[str, str], dict[str, Any]],
        commitments: list[dict[str, Any]],
        factory_stock: dict[str, float],
        source_stock: dict[str, float] | None = None,
        stock_fail: bool = False,
        commitments_mode: str = "ok",
    ) -> None:
        self.balances_ops = balances_ops
        self.standard_times = standard_times
        self.commitments = commitments
        self.factory_stock = factory_stock
        self.source_stock = source_stock or {}
        self.stock_fail = stock_fail
        # ok | missing_items | malformed | fail
        self.commitments_mode = commitments_mode
        self.stock_calls = 0
        self.commitment_calls = 0
        self.location_calls = 0
        self.inventory_block_calls = 0
        self.st_calls = 0

    def fetch_machine_load_operation_balances(self, *, branch: str, items: list[dict[str, str]]):
        out = []
        for item in items:
            key = (item["production_order"], item["operation_code"])
            row = self.balances_ops.get(key, {
                "operation_pending_qty": None,
                "operation_produced_qty": None,
            })
            out.append({"production_order": key[0], "operation_code": key[1], **row})
        return {"success": True, "data": {"items": out}}

    def fetch_operation_standard_time(self, *, branch: str, production_order: str, operation_code: str):
        self.st_calls += 1
        return self.standard_times[(production_order, operation_code)]

    def fetch_operation_materials_batch(self, *, branch: str, production_orders: list[str]):
        self.commitment_calls += 1
        if self.commitments_mode == "fail":
            raise DelpiGatewayError("empenhos offline")
        if self.commitments_mode == "missing_items":
            return {
                "success": True,
                "data": {
                    "branch": branch,
                    "production_orders": list(production_orders),
                    "summary": {"requested_count": len(production_orders)},
                },
            }
        if self.commitments_mode == "malformed":
            return "not-a-dict"
        wanted = set(production_orders)
        items = [
            row for row in self.commitments if row["production_order"] in wanted
        ]
        return {
            "success": True,
            "data": {
                "branch": branch,
                "production_orders": list(production_orders),
                "items": items,
                "summary": {
                    "requested_count": len(production_orders),
                    "returned_count": len(items),
                    "order_count": len({row["production_order"] for row in items}),
                },
            },
        }

    def fetch_stock_balances_items(
        self,
        *,
        branch: str,
        warehouse: str,
        only_positive: bool = True,
        page: int = 1,
        page_size: int = 500,
        product_codes: list[str] | None = None,
    ):
        self.stock_calls += 1
        if self.stock_fail:
            from production_control_app.domain.errors import DelpiGatewayError

            raise DelpiGatewayError("estoque offline")
        source = self.factory_stock if warehouse == "99" else self.source_stock
        wanted = set(product_codes or [])
        rows = [
            {"product_code": code, "quantity": qty, "warehouse": warehouse}
            for code, qty in source.items()
            if not wanted or code in wanted
        ]
        return {"success": True, "data": {"items": rows}}

    def fetch_product_physical_locations(self, *, branch: str, product_codes: list[str]):
        self.location_calls += 1
        return {"success": True, "data": {"items": []}}

    def fetch_product_inventory_blocks(
        self, *, branch: str, product_codes: list[str], warehouse: str = "01"
    ):
        self.inventory_block_calls += 1
        return {"success": True, "data": {"items": []}}


def _payload(ops: list[dict[str, Any]]) -> dict[str, Any]:
    centers = []
    for item in ops:
        if not any(c["work_center"] == item["work_center"] for c in centers):
            centers.append(
                {
                    "work_center": item["work_center"],
                    "work_center_name": item["work_center"],
                }
            )
    return {"work_centers": centers, "operations": ops}


def _op(work_center: str, order: str) -> dict[str, Any]:
    return {
        "work_center": work_center,
        "work_center_name": work_center,
        "production_order": order,
        "operation_code": "01",
        "product_code": f"P-{order}",
        "pa_product_code": f"PA-{order}",
        "unit": "PC",
        "pieces_conversion_factor": 1.0,
    }


def _horizon_ready_op(order: str = "OP1") -> dict[str, Any]:
    return {
        "published": _payload([_op("CT-A", order)]),
        "balances_ops": {
            (order, "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        },
        "standard_times": {
            (order, "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
    }


def _service(**kwargs: Any) -> LineFeederService:
    pubs = FakePublications()
    pubs.put("01", kwargs["published"])
    gateway = FakeGateway(
        balances_ops=kwargs["balances_ops"],
        standard_times=kwargs["standard_times"],
        commitments=kwargs["commitments"],
        factory_stock=kwargs["factory_stock"],
        source_stock=kwargs.get("source_stock") or {},
        stock_fail=kwargs.get("stock_fail", False),
        commitments_mode=kwargs.get("commitments_mode", "ok"),
    )
    from production_control_app.application.services.line_feeder_service import (
        _RequirementsCache,
    )

    return LineFeederService(
        gateway,  # type: ignore[arg-type]
        snapshots=FakeSnapshots(),  # type: ignore[arg-type]
        pick_plans=MagicMock(),
        publications=pubs,  # type: ignore[arg-type]
        branch_access=BranchAccessService(),
        cache=_RequirementsCache(0),
    )


def test_service_materials_preview_end_to_end() -> None:
    published = _payload([_op("CT-A", "OP1"), _op("CT-B", "OP2")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 60, "operation_produced_qty": 0},
            ("OP2", "01"): {"operation_pending_qty": 50, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
            ("OP2", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "Parafuso",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 60,
            },
            {
                "production_order": "OP2",
                "operation": "01",
                "product_code": "MP1",
                "description": "Parafuso",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 50,
            },
        ],
        factory_stock={"MP1": 40},
        source_stock={"MP1": 500},
    )
    # Horizonte grande: cobre as duas OPs inteiras (60+50 min < 3h).
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A", "CT-B"],
        hours_per_work_center=3,
    )
    assert data["operational_list_safe"] is True
    assert data["materials"][0]["required_qty"] == 110.0
    assert data["materials"][0]["to_collect_qty"] == 70.0
    assert data["business_rule"]["prior_pick_lists_do_not_reduce_demand"] is True


def test_service_stock_fail_not_safe() -> None:
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 10,
            }
        ],
        factory_stock={},
        stock_fail=True,
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert data["operational_list_safe"] is False
    assert "stock_unavailable" in data["stop_reasons"]
    assert data["materials"][0]["status"] == "unknown"


def test_service_stale_after_materials() -> None:
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 1,
            }
        ],
        factory_stock={"MP1": 0},
    )
    pubs = service._publications
    assert pubs is not None
    reads = {"n": 0}
    original = pubs.get

    def flaky(*, branch: str, conn=None):
        reads["n"] += 1
        row = original(branch=branch, conn=conn)
        # horizonte: 2 leituras; materiais: 3ª = checagem final → muta.
        if reads["n"] >= 3 and row is not None:
            return {**row, "row_version": "mutated"}
        return row

    pubs.get = flaky  # type: ignore[method-assign]
    with pytest.raises(HorizonPreviewStale):
        service.preview_materials(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )


def test_http_materials_preview() -> None:
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 10,
            }
        ],
        factory_stock={"MP1": 4},
        source_stock={"MP1": 100},
    )
    from production_control_app.interface.http.routes import line_feeder_routes

    original = line_feeder_routes.build_line_feeder_service
    line_feeder_routes.build_line_feeder_service = lambda: service  # type: ignore[assignment]
    try:
        app = FastAPI()

        @app.middleware("http")
        async def inject_user(request, call_next):  # noqa: ANN001
            request.state.user = _user(*FULL_PERMS)
            return await call_next(request)

        app.include_router(line_feeder_routes.router)
        client = TestClient(app)
        resp = client.post(
            "/line-feeder/materials/preview",
            json={
                "branch": "01",
                "workCenters": ["CT-A"],
                "hoursPerWorkCenter": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["materials"][0]["to_collect_qty"] == 6.0
    finally:
        line_feeder_routes.build_line_feeder_service = original  # type: ignore[assignment]


def test_rbac_denied() -> None:
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={},
        standard_times={},
        commitments=[],
        factory_stock={},
    )
    with pytest.raises(PermissionError):
        service.preview_materials(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )


# --------------------------------------------------------------------------- #
# Rework E3 — ausência legítima × falha de integração
# --------------------------------------------------------------------------- #


def test_validated_empty_items_is_legitimate_absence() -> None:
    items = validated_operation_materials_batch_items(
        {
            "success": True,
            "data": {
                "branch": "01",
                "production_orders": ["OP1"],
                "items": [],
                "summary": {
                    "requested_count": 1,
                    "returned_count": 0,
                    "order_count": 0,
                },
            },
        },
        branch="01",
        requested=["OP1"],
    )
    assert items == []


def test_validated_missing_items_key_is_invalid() -> None:
    assert (
        validated_operation_materials_batch_items(
            {
                "success": True,
                "data": {
                    "branch": "01",
                    "production_orders": ["OP1"],
                    "summary": {"requested_count": 1},
                },
            },
            branch="01",
            requested=["OP1"],
        )
        is None
    )


def test_validated_malformed_payload_is_invalid() -> None:
    assert (
        validated_operation_materials_batch_items(
            "broken", branch="01", requested=["OP1"]
        )
        is None
    )


def test_service_legitimate_no_commitments_is_safe() -> None:
    """Cenário A: consulta íntegra sem SD4 ativo — lista segura, sem MP inventada."""
    base = _horizon_ready_op("OP1")
    service = _service(
        **base,
        commitments=[],
        factory_stock={},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert data["operational_list_safe"] is True
    assert data["preview_completeness"] == "complete"
    assert data["materials"] == []
    assert "commitments_incomplete" not in data["stop_reasons"]
    assert any(w["code"] == "no_commitments" for w in data["demand_warnings"])


def test_service_missing_items_not_treated_as_absence() -> None:
    """Cenário B: sem items[] obrigatório — não é ausência legítima."""
    base = _horizon_ready_op("OP1")
    service = _service(
        **base,
        commitments=[],
        factory_stock={},
        commitments_mode="missing_items",
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert data["operational_list_safe"] is False
    assert "commitments_incomplete" in data["stop_reasons"]
    assert any(
        w["code"] == "commitments_response_invalid" for w in data["demand_warnings"]
    )


def test_service_malformed_commitments_not_safe() -> None:
    base = _horizon_ready_op("OP1")
    service = _service(
        **base,
        commitments=[],
        factory_stock={},
        commitments_mode="malformed",
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert data["operational_list_safe"] is False
    assert "commitments_incomplete" in data["stop_reasons"]


def test_service_commitments_batch_failure_raises() -> None:
    """Falha de integração em lote — erro controlado, não lista completa falsa."""
    base = _horizon_ready_op("OP1")
    service = _service(
        **base,
        commitments=[],
        factory_stock={},
        commitments_mode="fail",
    )
    with pytest.raises(DelpiGatewayError):
        service.preview_materials(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )


def test_domain_no_commitments_warning_keeps_proportional_ok() -> None:
    ops = [
        CoveredOperationDemand(
            work_center="CT-A",
            work_center_name="A",
            production_order="OP1",
            operation_code="01",
            operation_id="x",
            sequence_position=1,
            covered_qty=Decimal("10"),
            pending_qty=Decimal("10"),
        )
    ]
    buckets, warnings, ok = build_material_demands(ops, {})
    assert ok is True
    assert buckets == []
    assert warnings[0]["code"] == "no_commitments"


# --------------------------------------------------------------------------- #
# Etapa 1 — segurança / shortfall vs incomplete / early-stop
# --------------------------------------------------------------------------- #


def test_materials_shortfall_queue_remains_safe() -> None:
    """AC-01: fila menor que o horizonte, dados válidos → shortfall, lista segura."""
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 1,
            }
        ],
        factory_stock={"MP1": 0},
        source_stock={"MP1": 10},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=8,
    )
    assert data["horizon"]["work_centers"][0]["completeness"] == "shortfall"
    assert data["operational_list_safe"] is True
    assert data["materials"]
    assert "horizon_incomplete" not in data["stop_reasons"]


def test_materials_partial_horizon_uses_full_sd4_and_skips_later_ops() -> None:
    """AC-02/AC-03: parcial → required=open_qty; ops fora do horizonte não entram."""
    ops = [_op("CT-A", f"OP{i}") for i in range(1, 4)]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    service = _service(
        published=_payload(ops),
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
            ("OP2", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
            ("OP3", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 1400,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
            ("OP2", "01"): {
                "ideal_cycle_seconds": 1400,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
            ("OP3", "01"): {
                "ideal_cycle_seconds": 1400,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 100,
            },
            {
                "production_order": "OP2",
                "operation": "01",
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 80,
            },
            {
                "production_order": "OP3",
                "operation": "01",
                "product_code": "MP1",
                "description": "Aço",
                "unit": "KG",
                "product_type": "MP",
                "open_qty": 90,
            },
        ],
        factory_stock={"MP1": 70},
        source_stock={"MP1": 1000},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert data["operational_list_safe"] is True
    assert data["business_rule"]["material_demand"] == (
        "open_commitment_qty_of_contemplated_operations"
    )
    # Só OP1 entra (parcial); demanda = 100 kg, não 20% de 100.
    assert data["materials"][0]["required_qty"] == 100.0
    assert data["materials"][0]["to_collect_qty"] == 30.0
    origins = data["materials"][0]["origins"]
    assert len(origins) == 1
    assert origins[0]["production_order"] == "OP1"
    assert origins[0]["pa_product_code"] == "PA-OP1"
    assert origins[0]["required_qty"] == 100.0
    assert origins[0]["fraction"] == pytest.approx(0.2)
    assert origins[0]["demand_basis"] == "open_commitment"
    assert service._gateway.st_calls == 1


def test_materials_missing_standard_time_is_incomplete_not_shortfall() -> None:
    """AC-09: tempo padrão inválido → incomplete + diagnóstico."""
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": None,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "unavailable",
                "data_quality": "standard_time_unavailable",
            },
        },
        commitments=[],
        factory_stock={},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    assert data["operational_list_safe"] is False
    assert data["horizon"]["work_centers"][0]["completeness"] == "incomplete"
    assert data["horizon"]["work_centers"][0]["stop_reason"] == "standard_time_unavailable"
    assert data["diagnostics"]
    assert "tempo padrão" in (data["diagnostics"][0]["message"] or "").lower()


def test_materials_call_limit_does_not_become_shortfall(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-05: limite de ST após ops válidas → incomplete (não shortfall)."""
    ops = [_op("CT-A", f"OP{i}") for i in range(1, 4)]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    published = _payload(ops)
    balances = {
        (f"OP{i}", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0}
        for i in range(1, 4)
    }
    times = {
        (f"OP{i}", "01"): {
            "ideal_cycle_seconds": 60,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        }
        for i in range(1, 4)
    }
    service = _service(
        published=published,
        balances_ops=balances,
        standard_times=times,
        commitments=[],
        factory_stock={},
    )
    from production_control_app.application.services import line_feeder_service as lfs

    original = lfs.setting_int

    def limited(key: str, default: int) -> int:
        if key == "horizonMaxStandardTimeCalls":
            return 1
        return original(key, default)

    # setting_int é importado por nome no service — patch no módulo consumidor.
    monkeypatch.setattr(lfs, "setting_int", limited)
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=8,
    )

    group = data["horizon"]["work_centers"][0]
    assert group["completeness"] == "incomplete"
    assert group["stop_reason"] == "standard_time_call_limit"
    assert data["operational_list_safe"] is False
    assert any(
        d.get("code") == "standard_time_call_limit" for d in (data.get("diagnostics") or [])
    )


def test_materials_blocked_ct_skips_stock_and_commitments() -> None:
    """AC-06/AC-07: CT bloqueado → sem lista + sem consultas de material."""
    published = _payload([_op("CT-A", "OP1"), _op("CT-B", "OP2")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
            ("OP2", "01"): {"operation_pending_qty": None, "operation_produced_qty": None},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 10,
            }
        ],
        factory_stock={"MP1": 0},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A", "CT-B"],
        hours_per_work_center=1,
    )
    gateway = service._gateway
    assert data["operational_list_safe"] is False
    assert data["materials"] == []
    assert gateway.commitment_calls == 0
    assert gateway.stock_calls == 0
    assert gateway.location_calls == 0
    assert gateway.inventory_block_calls == 0
    assert any(d.get("work_center") == "CT-B" for d in data["diagnostics"])
    assert "timing" in data


def test_materials_upstream_unavailable_not_shortfall() -> None:
    """AC-03: falha de integração de ST → incomplete."""
    published = _payload([_op("CT-A", "OP1")])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {"operation_pending_qty": 5, "operation_produced_qty": 0},
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": None,
                "setup_seconds": None,
                "pieces_conversion_factor": None,
                "standard_time_source": "unavailable",
                "data_quality": "upstream_unavailable",
            },
        },
        commitments=[],
        factory_stock={},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    assert data["horizon"]["work_centers"][0]["completeness"] == "incomplete"
    assert data["horizon"]["work_centers"][0]["stop_reason"] == "upstream_unavailable"
    assert data["operational_list_safe"] is False


@pytest.mark.parametrize(
    ("op_factor", "st_factor", "produced", "expected_reason"),
    [
        (None, None, 0, "piece_conversion_unavailable"),
        (1.0, 1, None, "setup_uncertain"),
    ],
)
def test_materials_data_blocks_are_not_operationally_safe(
    op_factor: float | None,
    st_factor: float | None,
    produced: float | None,
    expected_reason: str,
) -> None:
    """AC-04: conversão ausente / setup incerto → lista insegura."""
    op = _op("CT-A", "OP1")
    if op_factor is None:
        op.pop("pieces_conversion_factor", None)
    else:
        op["pieces_conversion_factor"] = op_factor
    published = _payload([op])
    service = _service(
        published=published,
        balances_ops={
            ("OP1", "01"): {
                "operation_pending_qty": 5,
                "operation_produced_qty": produced,
            },
        },
        standard_times={
            ("OP1", "01"): {
                "ideal_cycle_seconds": 60,
                "setup_seconds": 30,
                "pieces_conversion_factor": st_factor,
                "standard_time_source": "shy_tempad",
                "data_quality": "complete",
            },
        },
        commitments=[],
        factory_stock={},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    assert data["operational_list_safe"] is False
    assert data["materials"] == []
    assert data["horizon"]["work_centers"][0]["completeness"] == "incomplete"
    assert data["horizon"]["work_centers"][0]["stop_reason"] == expected_reason
    assert any(d.get("stop_reason") == expected_reason for d in data["diagnostics"])


def test_materials_timing_payload_is_present_without_secrets() -> None:
    """AC-09: instrumentação de fases sem alterar o cálculo nem expor segredos."""
    ready = _horizon_ready_op("OP1")
    service = _service(
        **ready,
        commitments=[
            {
                "production_order": "OP1",
                "operation": "01",
                "product_code": "MP1",
                "description": "X",
                "unit": "PC",
                "product_type": "MP",
                "open_qty": 10,
            }
        ],
        factory_stock={"MP1": 0},
        source_stock={"MP1": 10},
    )
    data = service.preview_materials(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    timing = data["timing"]
    assert isinstance(timing, dict)
    assert "total_ms" in timing or "phases_ms" in timing
    blob = str(timing).lower()
    for forbidden in ("password", "secret", "authorization", "bearer ", "sql"):
        assert forbidden not in blob
    assert data["operational_list_safe"] is True
    assert data["materials"]

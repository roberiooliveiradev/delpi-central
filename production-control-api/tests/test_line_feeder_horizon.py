"""Etapa 2 — motor de horizonte do Alimentador de Linha."""

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
from production_control_app.domain.errors import HorizonPreviewStale, SnapshotNotFound
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.line_feeder_horizon import (
    HorizonOperationInput,
    allocate_work_center_horizon,
    horizon_needs_more_operations,
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


def _hop(
    *,
    order: str,
    pending: float,
    cycle: float,
    setup: float = 0.0,
    produced: float | None = 0.0,
    factor: float = 1.0,
    position: int = 1,
    quality: str = "complete",
    balance_state: str = "open",
    work_center: str = "CT-A",
) -> HorizonOperationInput:
    return HorizonOperationInput(
        operation_id=f"01|{work_center}|{order}|01",
        sequence_position=position,
        work_center=work_center,
        work_center_name=work_center,
        production_order=order,
        operation_code="01",
        product_code=f"P-{order}",
        unit="PC" if factor == 1 else "MI",
        pending_qty=None if balance_state == "unknown" else Decimal(str(pending)),
        produced_qty=None if produced is None else Decimal(str(produced)),
        balance_state=balance_state,
        ideal_cycle_seconds=Decimal(str(cycle)) if quality == "complete" else None,
        setup_seconds=Decimal(str(setup)),
        pieces_conversion_factor=Decimal(str(factor)),
        standard_time_quality=quality,
        standard_time_source="shy_tempad",
    )


# --------------------------------------------------------------------------- #
# Motor puro
# --------------------------------------------------------------------------- #


def test_allocate_two_hours_partial_third_operation() -> None:
    """30 + 60 min integrais + 1h restante: terceira (4×30 min) cobre 2 peças."""
    ops = [
        _hop(order="A", pending=1, cycle=1800, position=1),  # 30 min
        _hop(order="B", pending=1, cycle=3600, position=2),  # 60 min
        _hop(order="C", pending=4, cycle=1800, position=3),  # 4×30 min
    ]
    # Horizonte 2,5 h: sobram 60 min após A+B → 2 peças da terceira.
    result = allocate_work_center_horizon(ops, hours=2.5, work_center="CT-A")
    assert len(result.operations) == 3
    assert result.operations[0].coverage == "full"
    assert result.operations[1].coverage == "full"
    assert result.operations[2].coverage == "partial"
    assert result.operations[2].covered_qty == 2.0
    assert result.operations[2].remaining_outside_qty == 2.0
    assert result.seconds_covered == pytest.approx(9000.0)


def test_allocate_partial_quantity_within_horizon() -> None:
    """Operação com 4 peças de 30 min e horizonte 1h → 2 peças contempladas."""
    ops = [
        _hop(order="A", pending=4, cycle=1800, position=1),
    ]
    result = allocate_work_center_horizon(ops, hours=1, work_center="CT-A")
    assert len(result.operations) == 1
    op = result.operations[0]
    assert op.coverage == "partial"
    assert op.covered_qty == 2.0
    assert op.remaining_outside_qty == 2.0
    assert op.productive_seconds == 3600.0
    assert op.setup_seconds_applied == 0.0
    # Residual zero neste caso → complete; parcial com residual também é complete.
    assert result.completeness == "complete"
    assert horizon_needs_more_operations(result) is False


def test_allocate_partial_with_residual_is_not_queue_shortfall() -> None:
    """AC-01 domínio: parcial com sobra < 1 peça → complete (não queue_shorter)."""
    ops = [
        _hop(order="A", pending=10, cycle=1400, position=1),
        _hop(order="B", pending=10, cycle=1400, position=2),
    ]
    result = allocate_work_center_horizon(ops, hours=1, work_center="CT-A")
    assert len(result.operations) == 1
    assert result.operations[0].coverage == "partial"
    assert result.operations[0].covered_qty == 2.0
    assert result.seconds_covered == pytest.approx(2800.0)
    assert result.hours_shortfall == pytest.approx(800 / 3600)
    assert result.completeness == "complete"
    assert result.stop_reason is None
    assert horizon_needs_more_operations(result) is False


def test_three_work_centers_independent_budgets() -> None:
    """3h por CT não compartilha orçamento entre postos."""
    results = []
    for center in ("CT-A", "CT-B", "CT-C"):
        ops = [_hop(order=f"{center}-1", pending=10, cycle=3600, work_center=center)]
        results.append(
            allocate_work_center_horizon(ops, hours=3, work_center=center)
        )
    for result in results:
        assert result.hours_requested == 3.0
        assert result.operations[0].covered_qty == 3.0


def test_closed_operation_does_not_consume_budget() -> None:
    ops = [
        _hop(order="DONE", pending=0, cycle=3600, balance_state="closed", position=1),
        _hop(order="OPEN", pending=1, cycle=1800, position=2),
    ]
    result = allocate_work_center_horizon(ops, hours=1, work_center="CT-A")
    assert result.skipped_closed_count == 1
    assert result.operations[0].production_order == "OPEN"
    assert result.operations[0].covered_qty == 1.0


def test_mi_factor_1000_no_double_conversion() -> None:
    """1 MI com factor 1000 e ciclo 1s/peça → 1000s; horizonte 500s → 0.5 MI."""
    ops = [
        _hop(
            order="MI1",
            pending=1.0,
            cycle=1.0,
            factor=1000.0,
            position=1,
        )
    ]
    result = allocate_work_center_horizon(ops, hours=500 / 3600, work_center="CT-A")
    op = result.operations[0]
    assert op.pending_physical_pieces == 1000.0
    assert op.covered_physical_pieces == 500.0
    assert op.covered_qty == 0.5
    assert op.remaining_outside_qty == 0.5


def test_setup_applicable_then_waived_when_produced() -> None:
    with_setup = allocate_work_center_horizon(
        [_hop(order="NEW", pending=1, cycle=100, setup=50, produced=0.0)],
        hours=1,
        work_center="CT-A",
    )
    assert with_setup.operations[0].setup_seconds_applied == 50.0
    assert with_setup.operations[0].setup_policy == "applicable"

    started = allocate_work_center_horizon(
        [_hop(order="RUN", pending=1, cycle=100, setup=50, produced=2.0)],
        hours=1,
        work_center="CT-A",
    )
    assert started.operations[0].setup_seconds_applied == 0.0
    assert started.operations[0].setup_policy == "waived_produced"


def test_setup_uncertain_marks_incomplete() -> None:
    result = allocate_work_center_horizon(
        [_hop(order="U", pending=1, cycle=100, setup=30, produced=None)],
        hours=1,
        work_center="CT-A",
    )
    assert result.completeness == "incomplete"
    assert result.setup_uncertain is True
    assert result.operations[0].setup_policy == "uncertain"
    assert result.operations[0].setup_seconds_applied == 30.0


def test_invalid_standard_time_stops_without_skipping() -> None:
    ops = [
        _hop(order="BAD", pending=1, cycle=100, quality="standard_time_unavailable", position=1),
        _hop(order="OK", pending=1, cycle=100, position=2),
    ]
    result = allocate_work_center_horizon(ops, hours=2, work_center="CT-A")
    assert result.completeness == "incomplete"
    assert result.stop_reason == "standard_time_unavailable"
    assert result.operations == ()


def test_unknown_balance_stops() -> None:
    ops = [
        _hop(order="UNK", pending=1, cycle=100, balance_state="unknown", position=1),
        _hop(order="OK", pending=1, cycle=100, position=2),
    ]
    result = allocate_work_center_horizon(ops, hours=2, work_center="CT-A")
    assert result.completeness == "incomplete"
    assert result.stop_reason == "balance_unknown"
    assert result.operations == ()


def test_setup_does_not_fit_no_fictional_qty() -> None:
    result = allocate_work_center_horizon(
        [_hop(order="S", pending=10, cycle=60, setup=4000, produced=0.0)],
        hours=1,  # 3600s < 4000 setup
        work_center="CT-A",
    )
    assert result.operations == ()
    assert result.stop_reason == "insufficient_time_for_setup"
    assert result.completeness == "shortfall"


def test_short_queue_transparent_shortfall() -> None:
    result = allocate_work_center_horizon(
        [_hop(order="ONLY", pending=1, cycle=600)],
        hours=3,
        work_center="CT-A",
    )
    assert result.completeness == "shortfall"
    assert result.hours_shortfall == pytest.approx(3.0 - 600 / 3600)
    assert result.stop_reason == "queue_shorter_than_horizon"


# --------------------------------------------------------------------------- #
# Serviço / HTTP
# --------------------------------------------------------------------------- #


class FakePublications:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.get_count = 0

    def put(
        self,
        branch: str,
        payload: dict[str, Any],
        *,
        generation_id: str = "gen-1",
        row_version: str = "rev-1",
    ) -> None:
        self.rows[branch] = {
            "branch": branch,
            "generation_id": generation_id,
            "row_version": row_version,
            "start_date": date(2026, 9, 1),
            "end_date": date(2026, 9, 30),
            "payload_json": payload,
            "published_at": datetime(2026, 9, 20, 12, tzinfo=timezone.utc),
            "published_by": "pcp",
            "source_refreshed_at": datetime(2026, 9, 19, 10, tzinfo=timezone.utc),
        }

    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        self.get_count += 1
        return self.rows.get(branch)


class FakeSnapshots:
    def __init__(self) -> None:
        self.get_calls = 0
        self.rows: dict[str, Any] = {}

    def get(self, *, branch: str) -> dict[str, Any] | None:
        self.get_calls += 1
        return self.rows.get(branch)


class FakeGateway:
    def __init__(
        self,
        *,
        balances: dict[tuple[str, str], dict[str, Any]] | None = None,
        standard_times: dict[tuple[str, str], dict[str, Any]] | None = None,
        balances_fail: bool = False,
    ) -> None:
        self.balances = balances or {}
        self.standard_times = standard_times or {}
        self.balances_fail = balances_fail
        self.balance_calls = 0
        self.st_calls = 0

    def fetch_machine_load_operation_balances(self, *, branch: str, items: list[dict[str, str]]):
        self.balance_calls += 1
        if self.balances_fail:
            from production_control_app.domain.errors import DelpiGatewayError

            raise DelpiGatewayError("saldos indisponíveis", status_code=502)
        out = []
        for item in items:
            key = (item["production_order"], item["operation_code"])
            if key in self.balances:
                out.append({"production_order": key[0], "operation_code": key[1], **self.balances[key]})
            else:
                out.append(
                    {
                        "production_order": key[0],
                        "operation_code": key[1],
                        "operation_pending_qty": None,
                        "operation_produced_qty": None,
                    }
                )
        return {"success": True, "data": {"items": out}}

    def fetch_operation_standard_time(
        self, *, branch: str, production_order: str, operation_code: str
    ):
        self.st_calls += 1
        key = (production_order, operation_code)
        if key not in self.standard_times:
            return {
                "ideal_cycle_seconds": None,
                "setup_seconds": 0,
                "pieces_conversion_factor": 1,
                "standard_time_source": "unavailable",
                "data_quality": "standard_time_unavailable",
            }
        return self.standard_times[key]


def _payload(operations: list[dict[str, Any]]) -> dict[str, Any]:
    centers: list[dict[str, str]] = []
    for item in operations:
        code = item["work_center"]
        if not any(c["work_center"] == code for c in centers):
            centers.append(
                {"work_center": code, "work_center_name": item.get("work_center_name") or code}
            )
    return {"work_centers": centers, "operations": operations}


def _op_row(
    *,
    work_center: str,
    order: str,
    operation: str = "01",
    unit: str = "PC",
    factor: float = 1.0,
) -> dict[str, Any]:
    return {
        "work_center": work_center,
        "work_center_name": work_center,
        "production_order": order,
        "operation_code": operation,
        "product_code": f"P-{order}",
        "product_description": order,
        "unit": unit,
        "pieces_conversion_factor": factor,
        "operation_pending_qty": 10,
    }


def _service(
    *,
    published: dict[str, Any],
    balances: dict[tuple[str, str], dict[str, Any]],
    standard_times: dict[tuple[str, str], dict[str, Any]],
    row_version: str = "rev-1",
    working: dict[str, Any] | None = None,
) -> tuple[LineFeederService, FakePublications, FakeSnapshots, FakeGateway]:
    pubs = FakePublications()
    pubs.put("01", published, row_version=row_version)
    snaps = FakeSnapshots()
    if working is not None:
        snaps.rows["01"] = {"payload_json": working, "generation_id": "working"}
    gateway = FakeGateway(balances=balances, standard_times=standard_times)
    from production_control_app.application.services.line_feeder_service import (
        _RequirementsCache,
    )

    service = LineFeederService(
        gateway,  # type: ignore[arg-type]
        snapshots=snaps,  # type: ignore[arg-type]
        pick_plans=MagicMock(),
        publications=pubs,  # type: ignore[arg-type]
        branch_access=BranchAccessService(),
        cache=_RequirementsCache(0),
    )
    return service, pubs, snaps, gateway


def test_service_follows_published_order_not_working() -> None:
    published = _payload(
        [
            _op_row(work_center="CT-A", order="FIRST"),
            _op_row(work_center="CT-A", order="SECOND"),
        ]
    )
    working = _payload(
        [
            _op_row(work_center="CT-A", order="SECOND"),
            _op_row(work_center="CT-A", order="FIRST"),
            _op_row(work_center="CT-A", order="DRAFT"),
        ]
    )
    balances = {
        ("FIRST", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        ("SECOND", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {
        ("FIRST", "01"): {
            "ideal_cycle_seconds": 1800,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        },
        ("SECOND", "01"): {
            "ideal_cycle_seconds": 1800,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        },
    }
    service, _p, snaps, _g = _service(
        published=published, working=working, balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    orders = [op["production_order"] for op in data["work_centers"][0]["operations"]]
    assert orders == ["FIRST", "SECOND"]
    assert snaps.get_calls == 0


def test_service_live_partial_balance() -> None:
    published = _payload([_op_row(work_center="CT-A", order="OP1")])
    balances = {
        ("OP1", "01"): {"operation_pending_qty": 2, "operation_produced_qty": 3},
    }
    st = {
        ("OP1", "01"): {
            "ideal_cycle_seconds": 1800,
            "setup_seconds": 600,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        }
    }
    service, *_ = _service(published=published, balances=balances, standard_times=st)
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    op = data["work_centers"][0]["operations"][0]
    assert op["pending_qty"] == 2.0
    assert op["setup_seconds_applied"] == 0.0
    assert op["setup_policy"] == "waived_produced"
    assert op["covered_qty"] == 2.0


def test_service_stale_publication_conflict() -> None:
    published = _payload([_op_row(work_center="CT-A", order="OP1")])
    balances = {
        ("OP1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {
        ("OP1", "01"): {
            "ideal_cycle_seconds": 100,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        }
    }
    service, pubs, *_ = _service(
        published=published, balances=balances, standard_times=st, row_version="1"
    )
    original_get = pubs.get

    def flaky_get(*, branch: str, conn=None):
        row = original_get(branch=branch, conn=conn)
        if pubs.get_count >= 2 and row is not None:
            return {**row, "row_version": "changed"}
        return row

    pubs.get = flaky_get  # type: ignore[method-assign]
    with pytest.raises(HorizonPreviewStale):
        service.preview_horizon(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )


def test_service_no_publication() -> None:
    service, *_ = _service(
        published=_payload([]),
        balances={},
        standard_times={},
    )
    service._publications.rows.clear()  # type: ignore[union-attr]
    with pytest.raises(SnapshotNotFound):
        service.preview_horizon(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )


def test_service_rbac_and_invalid_input() -> None:
    published = _payload([_op_row(work_center="CT-A", order="OP1")])
    service, *_ = _service(published=published, balances={}, standard_times={})
    with pytest.raises(PermissionError):
        service.preview_horizon(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
            work_centers=["CT-A"],
            hours_per_work_center=1,
        )
    with pytest.raises(ValueError):
        service.preview_horizon(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-A", "CT-A"],
            hours_per_work_center=1,
        )
    with pytest.raises(ValueError):
        service.preview_horizon(
            _user(*FULL_PERMS),
            branch="01",
            work_centers=["CT-MISSING"],
            hours_per_work_center=1,
        )


def test_http_preview_envelope() -> None:
    published = _payload([_op_row(work_center="CT-A", order="OP1")])
    balances = {
        ("OP1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {
        ("OP1", "01"): {
            "ideal_cycle_seconds": 600,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "shy_tempad",
            "data_quality": "complete",
        }
    }
    service, *_ = _service(published=published, balances=balances, standard_times=st)
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
            "/line-feeder/horizon/preview",
            json={
                "branch": "01",
                "workCenters": ["CT-A"],
                "hoursPerWorkCenter": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["work_centers"][0]["operations"][0]["covered_qty"] == 1.0
        assert body["data"]["publication"]["publication_revision"]
    finally:
        line_feeder_routes.build_line_feeder_service = original  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Otimização Etapa 2 — consulta progressiva de tempo padrão
# --------------------------------------------------------------------------- #


def _complete_st(cycle: float = 3600) -> dict[str, Any]:
    return {
        "ideal_cycle_seconds": cycle,
        "setup_seconds": 0,
        "pieces_conversion_factor": 1,
        "standard_time_source": "shy_tempad",
        "data_quality": "complete",
    }


def test_horizon_needs_more_only_for_queue_shortfall() -> None:
    short = allocate_work_center_horizon(
        [_hop(order="ONLY", pending=1, cycle=600)],
        hours=3,
        work_center="CT-A",
    )
    assert short.completeness == "shortfall"
    assert horizon_needs_more_operations(short) is True

    filled = allocate_work_center_horizon(
        [_hop(order="FULL", pending=10, cycle=3600)],
        hours=1,
        work_center="CT-A",
    )
    assert filled.completeness == "complete"
    assert horizon_needs_more_operations(filled) is False

    bad = allocate_work_center_horizon(
        [_hop(order="BAD", pending=1, cycle=100, quality="standard_time_unavailable")],
        hours=1,
        work_center="CT-A",
    )
    assert bad.completeness == "incomplete"
    assert horizon_needs_more_operations(bad) is False


def test_progressive_stops_standard_time_after_horizon_covered() -> None:
    """AC-01: 55 ops, 5 cobrem 8h → só 5 consultas ST."""
    ops = [_op_row(work_center="CT-A", order=f"OP{i:02d}") for i in range(1, 56)]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    balances = {
        (f"OP{i:02d}", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0}
        for i in range(1, 56)
    }
    # 1 peça × 3600s = 1h; 5 ops = 5h… use 5760s ≈ 1.6h → 5 ops cobrem 8h.
    cycle = 5760
    st = {(f"OP{i:02d}", "01"): _complete_st(cycle) for i in range(1, 56)}
    # Marca ops 6+ como inválidas: se consultadas, incompletaría o CT.
    for i in range(6, 56):
        st[(f"OP{i:02d}", "01")] = {
            "ideal_cycle_seconds": None,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "unavailable",
            "data_quality": "standard_time_unavailable",
        }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=8,
    )
    assert gateway.st_calls == 5
    assert data["standard_time_calls"] == 5
    assert data["standard_time_calls_avoided"] == 50
    group = data["work_centers"][0]
    assert group["completeness"] == "complete"
    assert len(group["operations"]) == 5
    assert sum(op["covered_qty"] for op in group["operations"]) == pytest.approx(5.0)


def test_progressive_ignores_invalid_ops_beyond_horizon() -> None:
    """AC-02: op inválida depois do horizonte não é consultada."""
    ops = [
        _op_row(work_center="CT-A", order="OP1"),
        _op_row(work_center="CT-A", order="OP2"),
        _op_row(work_center="CT-A", order="BAD"),
    ]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    balances = {
        ("OP1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        ("OP2", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        ("BAD", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
    }
    st = {
        ("OP1", "01"): _complete_st(3600),
        ("OP2", "01"): _complete_st(3600),
        ("BAD", "01"): {
            "ideal_cycle_seconds": None,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "unavailable",
            "data_quality": "standard_time_unavailable",
        },
    }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    assert gateway.st_calls == 2
    assert data["standard_time_calls_avoided"] == 1
    assert data["work_centers"][0]["completeness"] == "complete"
    assert "BAD" not in {
        op["production_order"] for op in data["work_centers"][0]["operations"]
    }


def test_progressive_invalid_inside_horizon_is_incomplete() -> None:
    """AC-03: ST inválido na op necessária → incomplete."""
    ops = [
        _op_row(work_center="CT-A", order="BAD"),
        _op_row(work_center="CT-A", order="OK"),
    ]
    balances = {
        ("BAD", "01"): {"operation_pending_qty": 2, "operation_produced_qty": 0},
        ("OK", "01"): {"operation_pending_qty": 2, "operation_produced_qty": 0},
    }
    st = {
        ("BAD", "01"): {
            "ideal_cycle_seconds": None,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "unavailable",
            "data_quality": "standard_time_unavailable",
        },
        ("OK", "01"): _complete_st(3600),
    }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=2,
    )
    assert gateway.st_calls == 1
    assert data["work_centers"][0]["completeness"] == "incomplete"
    assert data["work_centers"][0]["stop_reason"] == "standard_time_unavailable"


def test_progressive_shortfall_when_queue_short() -> None:
    """AC-04: fila válida menor que o horizonte → shortfall."""
    published = _payload([_op_row(work_center="CT-A", order="ONLY")])
    balances = {
        ("ONLY", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {("ONLY", "01"): _complete_st(1800)}
    service, _, _, gateway = _service(
        published=published, balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=3,
    )
    assert gateway.st_calls == 1
    assert data["work_centers"][0]["completeness"] == "shortfall"
    assert data["work_centers"][0]["stop_reason"] == "queue_shorter_than_horizon"


def test_progressive_partial_operation_matches_batch_motor() -> None:
    """AC-05: cobertura parcial equivalente ao motor canônico em lote."""
    ops = [
        _op_row(work_center="CT-A", order="OP1"),
        _op_row(work_center="CT-A", order="OP2"),
    ]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    balances = {
        ("OP1", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
        ("OP2", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0},
    }
    st = {
        ("OP1", "01"): _complete_st(1800),
        ("OP2", "01"): _complete_st(1800),
    }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    # 1h = 3600s → 2 peças de 1800s na OP1; OP2 fora.
    assert gateway.st_calls == 1
    group = data["work_centers"][0]
    assert group["completeness"] == "complete"
    assert len(group["operations"]) == 1
    assert group["operations"][0]["coverage"] == "partial"
    assert group["operations"][0]["covered_qty"] == 2.0
    batch = allocate_work_center_horizon(
        [
            _hop(order="OP1", pending=10, cycle=1800, position=1),
            _hop(order="OP2", pending=10, cycle=1800, position=2),
        ],
        hours=1,
        work_center="CT-A",
    )
    assert group["operations"][0]["covered_qty"] == batch.operations[0].covered_qty
    assert group["operations"][0]["offset_end_seconds"] == batch.operations[0].offset_end_seconds


def test_progressive_partial_with_residual_skips_later_standard_times() -> None:
    """AC-01: 3600s, ciclo 1400s, 10 pendentes + ops posteriores → 1 ST apenas."""
    ops = [_op_row(work_center="CT-A", order=f"OP{i}") for i in range(1, 6)]
    for index, op in enumerate(ops, start=1):
        op["sequence_position"] = index
    balances = {
        (f"OP{i}", "01"): {"operation_pending_qty": 10, "operation_produced_qty": 0}
        for i in range(1, 6)
    }
    st = {(f"OP{i}", "01"): _complete_st(1400) for i in range(1, 6)}
    # Se consultasse OP2+, inventaria incompleto — prova que não consultou.
    for i in range(2, 6):
        st[(f"OP{i}", "01")] = {
            "ideal_cycle_seconds": None,
            "setup_seconds": 0,
            "pieces_conversion_factor": 1,
            "standard_time_source": "unavailable",
            "data_quality": "standard_time_unavailable",
        }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A"],
        hours_per_work_center=1,
    )
    assert gateway.st_calls == 1
    assert data["standard_time_calls"] == 1
    assert data["standard_time_calls_avoided"] == 4
    group = data["work_centers"][0]
    assert group["completeness"] == "complete"
    assert group["stop_reason"] is None
    assert len(group["operations"]) == 1
    assert group["operations"][0]["coverage"] == "partial"
    assert group["operations"][0]["covered_qty"] == 2.0


def test_progressive_multi_ct_independent_budgets() -> None:
    """AC-06: cada CT encerra suas próprias consultas ST."""
    ops = [
        *[_op_row(work_center="CT-A", order=f"A{i}") for i in range(1, 6)],
        *[_op_row(work_center="CT-B", order=f"B{i}") for i in range(1, 4)],
        *[_op_row(work_center="CT-C", order=f"C{i}") for i in range(1, 8)],
    ]
    balances = {
        (op["production_order"], "01"): {
            "operation_pending_qty": 1,
            "operation_produced_qty": 0,
        }
        for op in ops
    }
    st = {
        (op["production_order"], "01"): _complete_st(3600) for op in ops
    }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A", "CT-B", "CT-C"],
        hours_per_work_center=2,
    )
    # 2h ⇒ 2 ST por CT (cycle 1h).
    assert gateway.st_calls == 6
    assert data["standard_time_calls"] == 6
    by_ct = {g["work_center"]: g for g in data["work_centers"]}
    assert len(by_ct["CT-A"]["operations"]) == 2
    assert len(by_ct["CT-B"]["operations"]) == 2
    assert len(by_ct["CT-C"]["operations"]) == 2
    assert by_ct["CT-A"]["completeness"] == "complete"
    assert by_ct["CT-B"]["completeness"] == "complete"
    assert by_ct["CT-C"]["completeness"] == "complete"


def test_progressive_global_call_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-07: limite global conta apenas chamadas efetivas."""
    ops = [
        _op_row(work_center="CT-A", order="A1"),
        _op_row(work_center="CT-A", order="A2"),
        _op_row(work_center="CT-B", order="B1"),
    ]
    balances = {
        ("A1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        ("A2", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
        ("B1", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {
        ("A1", "01"): _complete_st(600),
        ("A2", "01"): _complete_st(600),
        ("B1", "01"): _complete_st(600),
    }
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    from production_control_app.application.services import line_feeder_service as lfs

    original = lfs.setting_int

    def limited(key: str, default: int) -> int:
        if key == "horizonMaxStandardTimeCalls":
            return 1
        return original(key, default)

    monkeypatch.setattr(lfs, "setting_int", limited)
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A", "CT-B"],
        hours_per_work_center=8,
    )
    assert gateway.st_calls == 1
    assert data["standard_time_calls"] == 1
    # CT-A consome o único call; A2 ou CT-B fica incomplete por limite.
    statuses = {g["work_center"]: g["completeness"] for g in data["work_centers"]}
    assert "incomplete" in statuses.values()
    assert any(
        g.get("stop_reason") == "standard_time_call_limit" for g in data["work_centers"]
    )


def test_progressive_reuses_standard_time_cache_across_cts() -> None:
    """Mesma OP/operação em CTs distintos reusa o cache da requisição."""
    # Na prática a mesma OP não aparece em dois CTs; o cache é por (OP, op_code).
    ops = [
        _op_row(work_center="CT-A", order="SHARED"),
        _op_row(work_center="CT-B", order="SHARED"),
    ]
    balances = {
        ("SHARED", "01"): {"operation_pending_qty": 1, "operation_produced_qty": 0},
    }
    st = {("SHARED", "01"): _complete_st(1800)}
    service, _, _, gateway = _service(
        published=_payload(ops), balances=balances, standard_times=st
    )
    data = service.preview_horizon(
        _user(*FULL_PERMS),
        branch="01",
        work_centers=["CT-A", "CT-B"],
        hours_per_work_center=1,
    )
    assert gateway.st_calls == 1
    assert data["standard_time_calls"] == 1

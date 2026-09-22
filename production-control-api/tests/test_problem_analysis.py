from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.detectors.incomplete_order_sets_detector import (
    DETECTOR_ID,
    IncompleteOrderSetsDetector,
)
from production_control_app.application.services.detectors.order_set_quantity_mismatches_detector import (
    DETECTOR_ID as QTY_DETECTOR_ID,
    OrderSetQuantityMismatchesDetector,
)
from production_control_app.application.services.detectors.uncovered_demand_detector import (
    DETECTOR_ID as DEMAND_DETECTOR_ID,
    UncoveredDemandDetector,
)
from production_control_app.application.services.detectors.shared_structure_intermediates_detector import (
    DETECTOR_ID as SHARED_DETECTOR_ID,
    SharedStructureIntermediatesDetector,
)
from production_control_app.application.services.demand_service import (
    DemandService,
    _DemandSnapshotCache,
)
from production_control_app.domain.services.demand_coverage_service import (
    DemandCoverageService,
)
from production_control_app.application.services.problem_analysis_service import (
    ProblemAnalysisService,
)
from production_control_app.application.services.problem_analysis_settings import (
    detector_catalog,
    detector_entry,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    DetectorNotFound,
    InvalidBranch,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.delayed_order_mapper import map_delayed_order


def _user(*permissions: str, superadmin: bool = False):
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


FULL_PERMS = (
    "production-control.access",
    "production-control.problem-analysis.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _set_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "branch": "01",
        "set_number": "108404",
        "set_item": "01",
        "set_key": "10840401",
        "root_code": "90262910",
        "root_description": "CHICOTE",
        "root_order": "10840401001",
        "due_date": "2026-08-21",
        "issued_at": "2026-07-01",
        "order_count": 4,
        "open_order_count": 3,
        "expected_component_count": 5,
        "created_component_count": 3,
        "missing_count": 2,
        "extra_count": 0,
        "missing_components": [
            {"product_code": "50320064", "description": "PI A", "bom_level": 1},
            {"product_code": "50320070", "description": "PI B", "bom_level": 2},
        ],
        "extra_components": [],
    }
    row.update(overrides)
    return row


class FakeSetsGateway:
    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
        summary: dict[str, Any] | None = None,
        *,
        quantity_items: list[dict[str, Any]] | None = None,
        quantity_summary: dict[str, Any] | None = None,
        shared_items: list[dict[str, Any]] | None = None,
        shared_summary: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.items = items or []
        self.summary = summary or {
            "checked_set_count": 500,
            "incomplete_set_count": len(self.items),
            "missing_set_count": len(self.items),
            "extra_set_count": 0,
        }
        self.quantity_items = quantity_items or []
        self.quantity_summary = quantity_summary or {
            "checked_set_count": 500,
            "mismatch_set_count": len(self.quantity_items),
            "under_set_count": len(self.quantity_items),
            "over_set_count": 0,
        }
        self.shared_items = shared_items or []
        self.shared_summary = shared_summary or {
            "checked_pa_count": 10,
            "shared_intermediate_count": len(self.shared_items),
            "max_shared_pa_count": 2 if self.shared_items else 0,
        }
        self.error = error
        self.calls: list[dict[str, Any]] = []
        self.sales_orders: list[dict[str, Any]] = []
        self.production_orders: list[dict[str, Any]] = []

    def fetch_production_order_sets_incomplete(
        self,
        *,
        branch: str,
        issued_from: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "kind": "incomplete",
                "branch": branch,
                "issued_from": issued_from,
                "page": page,
                "page_size": page_size,
            }
        )
        if self.error is not None:
            raise self.error
        return {
            "success": True,
            "data": {
                "items": self.items,
                "summary": self.summary,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": self.summary["incomplete_set_count"],
                },
            },
        }

    def fetch_production_order_sets_quantity_mismatches(
        self,
        *,
        branch: str,
        issued_from: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "kind": "quantity",
                "branch": branch,
                "issued_from": issued_from,
                "page": page,
                "page_size": page_size,
            }
        )
        if self.error is not None:
            raise self.error
        return {
            "success": True,
            "data": {
                "items": self.quantity_items,
                "summary": self.quantity_summary,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": self.quantity_summary["mismatch_set_count"],
                },
            },
        }

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        self.calls.append({"kind": "sales_orders"})
        if self.error is not None:
            raise self.error
        return {"data": {"items": self.sales_orders, "summary": {}}}

    def fetch_open_production_orders(self) -> dict[str, Any]:
        self.calls.append({"kind": "production_orders"})
        if self.error is not None:
            raise self.error
        return {"data": {"items": self.production_orders, "resumo": []}}

    def fetch_production_shared_structure_intermediates(
        self,
        *,
        branch: str,
        movement_from: str,
        lookback_days: int,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "kind": "shared_structure",
                "branch": branch,
                "movement_from": movement_from,
                "lookback_days": lookback_days,
                "page": page,
                "page_size": page_size,
            }
        )
        if self.error is not None:
            raise self.error
        return {
            "success": True,
            "data": {
                "items": self.shared_items,
                "summary": self.shared_summary,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": self.shared_summary["shared_intermediate_count"],
                },
            },
        }


def _qty_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "branch": "01",
        "set_number": "247192",
        "set_item": "01",
        "set_key": "24719201",
        "root_code": "90263364",
        "root_description": "CABO",
        "root_order": "24719201001",
        "root_quantity": 2.0,
        "due_date": "2026-08-24",
        "issued_at": "2026-08-12",
        "order_count": 3,
        "open_order_count": 3,
        "under_count": 1,
        "over_count": 0,
        "under_components": [
            {
                "product_code": "50090002",
                "description": "SEPARADOR",
                "product_type": "PI",
                "bom_level": 2,
                "production_order": "24719201003",
                "expected_quantity": 4.0,
                "actual_quantity": 2.0,
                "delta_quantity": -2.0,
            }
        ],
        "over_components": [],
    }
    row.update(overrides)
    return row


def _shared_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "intermediate_code": "50320064",
        "intermediate_description": "PI COMPARTILHADO",
        "intermediate_type": "PI",
        "shared_pa_count": 2,
        "finished_products": [
            {"product_code": "90262910", "description": "PA A", "bom_level": 1},
            {"product_code": "90262911", "description": "PA B", "bom_level": 2},
        ],
    }
    row.update(overrides)
    return row


def _service(gateway: FakeSetsGateway, **detector_kwargs: Any) -> ProblemAnalysisService:
    settings = detector_entry(DETECTOR_ID) or {}
    detector = IncompleteOrderSetsDetector(gateway, settings=settings, **detector_kwargs)
    return ProblemAnalysisService({DETECTOR_ID: detector})


# --------------------------------------------------------------- delayed order


def test_map_delayed_order_severity_from_days() -> None:
    critical = map_delayed_order(
        {
            "production_order": "000010",
            "op_key": "01|000010",
            "product_code": "90300005",
            "days_late": 8,
            "planned_qty": 10,
        },
        critical_days=7,
        title_template="OP {order} atrasada ({days} dias)",
    )
    assert critical["id"] == "delayed-order:01|000010"
    assert critical["severity"] == "critical"
    assert "000010" in critical["title"]

    attention = map_delayed_order(
        {"production_order": "2", "op_key": "01|2", "days_late": 2},
        critical_days=7,
        title_template="OP {order} atrasada ({days} dias)",
    )
    assert attention["severity"] == "attention"


# -------------------------------------------------------------------- catálogo


def test_catalog_declares_incomplete_order_sets_detector() -> None:
    ids = [entry["id"] for entry in detector_catalog()]
    assert DETECTOR_ID in ids
    assert QTY_DETECTOR_ID in ids
    assert DEMAND_DETECTOR_ID in ids
    assert SHARED_DETECTOR_ID in ids
    entry = detector_entry(DETECTOR_ID)
    assert entry is not None
    assert entry["title"]
    assert entry["description"]
    qty_entry = detector_entry(QTY_DETECTOR_ID)
    assert qty_entry is not None
    assert qty_entry["title"] == "Quantidades incorretas"
    demand_entry = detector_entry(DEMAND_DETECTOR_ID)
    assert demand_entry is not None
    assert demand_entry["title"] == "Demanda sem cobertura"
    shared_entry = detector_entry(SHARED_DETECTOR_ID)
    assert shared_entry is not None
    assert shared_entry["title"] == "Intermediários compartilhados"


def test_cards_come_from_catalog_and_detector_summary() -> None:
    gateway = FakeSetsGateway()
    result = _service(gateway).list_detectors(_user(*FULL_PERMS), branch="01")
    card = result["detectors"][0]
    assert card["id"] == DETECTOR_ID
    assert card["title"] == (detector_entry(DETECTOR_ID) or {})["title"]
    assert card["count"] == 0
    assert card["severity"] == "ok"
    assert result["summary"]["detector_count"] == 1
    # O card só precisa dos totais: nada de puxar a lista inteira.
    assert gateway.calls[0]["page_size"] == 1


def test_card_severity_is_critical_when_components_are_missing() -> None:
    gateway = FakeSetsGateway(
        [_set_row()],
        summary={
            "checked_set_count": 400,
            "incomplete_set_count": 3,
            "missing_set_count": 2,
            "extra_set_count": 1,
        },
    )
    result = _service(gateway).list_detectors(_user(*FULL_PERMS), branch="01")
    card = result["detectors"][0]
    assert card["severity"] == "critical"
    assert card["count"] == 3
    assert card["metrics"]["checked_set_count"] == 400


def test_card_severity_is_attention_when_only_extra_components() -> None:
    gateway = FakeSetsGateway(
        summary={
            "checked_set_count": 400,
            "incomplete_set_count": 2,
            "missing_set_count": 0,
            "extra_set_count": 2,
        }
    )
    result = _service(gateway).list_detectors(_user(*FULL_PERMS), branch="01")
    assert result["detectors"][0]["severity"] == "attention"


# --------------------------------------------------------------------- itens


def test_detector_items_map_set_severity_and_counts() -> None:
    extra_row = _set_row(
        set_number="112207",
        set_key="11220701",
        missing_count=0,
        extra_count=1,
        missing_components=[],
        extra_components=[
            {
                "product_code": "50319902",
                "description": "PI X",
                "production_order": "11220703",
            }
        ],
    )
    gateway = FakeSetsGateway([_set_row(), extra_row])
    payload = _service(gateway).detector_items(
        _user(*FULL_PERMS), branch="01", detector_id=DETECTOR_ID
    )
    missing_item, extra_item = payload["items"]
    assert missing_item["id"] == f"{DETECTOR_ID}:01|10840401"
    assert missing_item["severity"] == "critical"
    assert missing_item["missing_count"] == 2
    assert extra_item["severity"] == "attention"
    assert extra_item["extra_count"] == 1
    assert payload["detector"]["id"] == DETECTOR_ID
    assert payload["pagination"]["page"] == 1


def test_issued_from_narrows_the_window_by_configuration() -> None:
    gateway = FakeSetsGateway()
    detector = IncompleteOrderSetsDetector(
        gateway,
        settings={"issuedFromDays": 730},
        today=date(2026, 8, 20),
    )
    detector.summarize(branch="01")
    assert gateway.calls[0]["issued_from"] == "2024-08-20"


def test_zero_issued_from_days_disables_the_window() -> None:
    gateway = FakeSetsGateway()
    IncompleteOrderSetsDetector(gateway, settings={"issuedFromDays": 0}).summarize(branch="01")
    assert gateway.calls[0]["issued_from"] is None


def test_excluded_component_codes_drop_the_set_without_code_change() -> None:
    row = _set_row(
        missing_components=[{"product_code": "50320064", "description": "PI comprado"}],
        extra_components=[],
    )
    gateway = FakeSetsGateway([row])
    detector = IncompleteOrderSetsDetector(
        gateway, settings={"excludedComponentCodes": ["50320064"]}
    )
    page = detector.collect(branch="01", page=1, page_size=50)
    assert page.items == []


def test_excluded_root_prefixes_drop_the_set() -> None:
    gateway = FakeSetsGateway([_set_row(root_code="90262910")])
    detector = IncompleteOrderSetsDetector(
        gateway, settings={"excludedRootPrefixes": ["9026"]}
    )
    assert detector.collect(branch="01", page=1, page_size=50).items == []


# ------------------------------------------------------------------- guardas


def test_unknown_detector_is_rejected() -> None:
    service = _service(FakeSetsGateway())
    with pytest.raises(DetectorNotFound):
        service.detector_items(_user(*FULL_PERMS), branch="01", detector_id="nao-existe")


def test_missing_permission_is_rejected() -> None:
    service = _service(FakeSetsGateway())
    user = _user("production-control.access", "production-control.view.filial-01")
    with pytest.raises(PermissionError):
        service.list_detectors(user, branch="01")


def test_gateway_failure_surfaces_as_gateway_error() -> None:
    service = _service(FakeSetsGateway(error=RuntimeError("boom")))
    with pytest.raises(DelpiGatewayError):
        service.list_detectors(_user(*FULL_PERMS), branch="01")


# ---------------------------------------------------------------------- HTTP


def _client(gateway: FakeSetsGateway, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from production_control_app.composition import pc_composer
    from production_control_app.interface.http.routes import problem_analysis_routes

    test_app = FastAPI()

    @test_app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = _user(*FULL_PERMS)
        return await call_next(request)

    test_app.include_router(problem_analysis_routes.router)
    monkeypatch.setattr(pc_composer, "DelpiProductionGateway", lambda: gateway)
    return TestClient(test_app)


def test_routes_expose_cards_and_detector_items(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = FakeSetsGateway([_set_row()])
    client = _client(gateway, monkeypatch)

    cards = client.get("/problem-analysis", params={"branch": "01"})
    assert cards.status_code == 200
    body = cards.json()
    assert body["success"] is True
    assert body["data"]["detectors"][0]["id"] == DETECTOR_ID

    items = client.get(f"/problem-analysis/{DETECTOR_ID}", params={"branch": "01"})
    assert items.status_code == 200
    payload = items.json()["data"]
    assert payload["items"][0]["set_key"] == "10840401"
    assert payload["pagination"]["page"] == 1

    assert client.get("/problem-analysis/nao-existe", params={"branch": "01"}).status_code == 404
    assert client.get("/problem-analysis", params={"branch": "99"}).status_code == 422


def test_quantity_mismatch_detector_maps_under_and_over() -> None:
    over_row = _qty_row(
        under_count=0,
        over_count=1,
        under_components=[],
        over_components=[
            {
                "product_code": "50319902",
                "description": "CHICOTE",
                "product_type": "PI",
                "bom_level": 1,
                "production_order": "24719201004",
                "expected_quantity": 2.0,
                "actual_quantity": 3.0,
                "delta_quantity": 1.0,
            }
        ],
    )
    gateway = FakeSetsGateway(quantity_items=[_qty_row(), over_row])
    settings = detector_entry(QTY_DETECTOR_ID) or {}
    detector = OrderSetQuantityMismatchesDetector(gateway, settings=settings)
    service = ProblemAnalysisService({QTY_DETECTOR_ID: detector})
    payload = service.detector_items(
        _user(*FULL_PERMS), branch="01", detector_id=QTY_DETECTOR_ID
    )
    under_item, over_item = payload["items"]
    assert under_item["id"] == f"{QTY_DETECTOR_ID}:01|24719201"
    assert under_item["severity"] == "critical"
    assert under_item["under_count"] == 1
    assert under_item["under_components"][0]["expected_quantity"] == 4.0
    assert over_item["severity"] == "attention"
    assert over_item["over_count"] == 1

    cards = service.list_detectors(_user(*FULL_PERMS), branch="01")
    assert cards["detectors"][0]["metrics"]["under_set_count"] == 2


def test_routes_expose_quantity_mismatch_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = FakeSetsGateway(quantity_items=[_qty_row()])
    client = _client(gateway, monkeypatch)

    cards = client.get("/problem-analysis", params={"branch": "01"})
    assert cards.status_code == 200
    ids = [item["id"] for item in cards.json()["data"]["detectors"]]
    assert DETECTOR_ID in ids
    assert QTY_DETECTOR_ID in ids

    items = client.get(f"/problem-analysis/{QTY_DETECTOR_ID}", params={"branch": "01"})
    assert items.status_code == 200
    payload = items.json()["data"]
    assert payload["items"][0]["set_key"] == "24719201"
    assert payload["items"][0]["root_quantity"] == 2.0


def test_uncovered_demand_detector_flags_hole_and_late_op() -> None:
    gateway = FakeSetsGateway()
    gateway.sales_orders = [
        {
            "nome_cliente": "CLIENTE A",
            "tipo_entidade": "CLIENTE",
            "tipo_pedido": "N",
            "pedido_cliente": "PO-1",
            "filial": "01",
            "pedido": "045123",
            "linha": "01",
            "produto": "90262910",
            "codigo_cliente": "C001",
            "codigo_cadastro": "000123",
            "loja_cadastro": "01",
            "quantidade": 100.0,
            "entregue": 40.0,
            "saldo": 60.0,
            "data_despacho": "2026-08-20",
            "data_entrega": "2026-08-25",
            "no_estoque": 0.0,
        },
        {
            "nome_cliente": "CLIENTE B",
            "tipo_entidade": "CLIENTE",
            "tipo_pedido": "N",
            "pedido_cliente": "PO-2",
            "filial": "01",
            "pedido": "045124",
            "linha": "01",
            "produto": "90262911",
            "codigo_cliente": "C002",
            "codigo_cadastro": "000124",
            "loja_cadastro": "01",
            "quantidade": 10.0,
            "entregue": 0.0,
            "saldo": 10.0,
            "data_despacho": "2026-08-20",
            "data_entrega": "2026-08-22",
            "no_estoque": 0.0,
        },
    ]
    gateway.production_orders = [
        {
            "filial": "01",
            "numero_op": "10840401001",
            "produto": "90262911",
            "saldo_op": 10.0,
            "data_fim_prevista_op": "2026-08-30",
        }
    ]
    demand = DemandService(
        gateway,
        today=date(2026, 8, 21),
        coverage=DemandCoverageService(today=date(2026, 8, 21)),
        cache=_DemandSnapshotCache(0),
    )
    detector = UncoveredDemandDetector(
        gateway,
        settings=detector_entry(DEMAND_DETECTOR_ID) or {},
        today=date(2026, 8, 21),
        demand_service=demand,
    )
    page = detector.collect(branch="01", page=1, page_size=50)
    assert page.total == 2
    kinds = {item["issue_kind"] for item in page.items}
    assert kinds == {"uncovered", "late_op"}
    uncovered = next(item for item in page.items if item["issue_kind"] == "uncovered")
    assert uncovered["severity"] == "critical"
    assert uncovered["uncovered_quantity"] == 60.0
    late_op = next(item for item in page.items if item["issue_kind"] == "late_op")
    assert late_op["severity"] == "attention"
    summary = detector.summarize(branch="01")
    assert summary.severity == "critical"
    assert summary.metrics["uncovered_line_count"] == 1
    assert summary.metrics["late_op_line_count"] == 1


def test_routes_expose_uncovered_demand_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = FakeSetsGateway()
    gateway.sales_orders = [
        {
            "nome_cliente": "CLIENTE A",
            "tipo_entidade": "CLIENTE",
            "tipo_pedido": "N",
            "pedido_cliente": "PO-1",
            "filial": "01",
            "pedido": "045123",
            "linha": "01",
            "produto": "90262910",
            "codigo_cliente": "C001",
            "codigo_cadastro": "000123",
            "loja_cadastro": "01",
            "quantidade": 100.0,
            "entregue": 40.0,
            "saldo": 60.0,
            "data_despacho": "2026-08-20",
            "data_entrega": "2026-08-25",
            "no_estoque": 0.0,
        }
    ]
    client = _client(gateway, monkeypatch)
    cards = client.get("/problem-analysis", params={"branch": "01"})
    ids = [item["id"] for item in cards.json()["data"]["detectors"]]
    assert DEMAND_DETECTOR_ID in ids

    items = client.get(f"/problem-analysis/{DEMAND_DETECTOR_ID}", params={"branch": "01"})
    assert items.status_code == 200
    payload = items.json()["data"]
    assert payload["items"][0]["product_code"] == "90262910"
    assert payload["items"][0]["issue_kind"] == "uncovered"


def test_shared_structure_detector_maps_items() -> None:
    gateway = FakeSetsGateway(shared_items=[_shared_row()])
    settings = detector_entry(SHARED_DETECTOR_ID) or {}
    detector = SharedStructureIntermediatesDetector(
        gateway,
        settings=settings,
        today=date(2026, 9, 21),
    )
    page = detector.collect(branch="01", page=1, page_size=50)
    assert page.total == 1
    item = page.items[0]
    assert item["intermediate_code"] == "50320064"
    assert item["severity"] == "attention"
    assert len(item["finished_products"]) == 2
    summary = detector.summarize(branch="01")
    assert summary.metrics["checked_pa_count"] == 10
    assert gateway.calls[0]["movement_from"] == "2025-09-21"


def test_routes_expose_shared_structure_detector(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = FakeSetsGateway(shared_items=[_shared_row()])
    client = _client(gateway, monkeypatch)
    cards = client.get("/problem-analysis", params={"branch": "01"})
    ids = [item["id"] for item in cards.json()["data"]["detectors"]]
    assert SHARED_DETECTOR_ID in ids

    items = client.get(f"/problem-analysis/{SHARED_DETECTOR_ID}", params={"branch": "01"})
    assert items.status_code == 200
    payload = items.json()["data"]
    assert payload["items"][0]["intermediate_code"] == "50320064"
    assert payload["items"][0]["shared_pa_count"] == 2


def test_branch_gate_rejects_other_filial() -> None:
    service = BranchAccessService()
    user = _user(
        "production-control.access",
        "production-control.view.filial-01",
    )
    service.assert_can_view_branch(user, "01")
    with pytest.raises(BranchAccessDenied):
        service.assert_can_view_branch(user, "02")
    with pytest.raises(InvalidBranch):
        service.assert_can_view_branch(user, "99")

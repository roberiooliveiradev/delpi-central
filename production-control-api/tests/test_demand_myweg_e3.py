"""Etapa 3 — integração MyWEG em GET /demand (origin filter)."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.demand_service import (
    ORIGIN_BOTH,
    ORIGIN_MYWEG,
    ORIGIN_PROTHEUS,
    DemandService,
    _DemandSnapshotCache,
)
from production_control_app.application.services.myweg_demand_coverage_preview_service import (
    MyWegDemandCoveragePreviewService,
)
from production_control_app.application.services.myweg_demand_source_service import (
    MyWegDemandSourceService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_01,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.errors import InvalidBranch
from production_control_app.domain.services.demand_coverage_service import (
    DemandCoverageService,
)
from production_control_app.domain.services.myweg_demand_coverage_adapter import (
    OP_UNIT_UNVERIFIED,
)

TODAY = date(2026, 11, 8)


def _user(*perms: str) -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=False, permissions=set(perms))


class _FakeRepo:
    def __init__(self, batch: dict, rows: list[dict]) -> None:
        self.batch = batch
        self.rows = rows

    def get_latest_batch(self) -> dict | None:
        return self.batch

    def list_batch_records_for_compare(self, *, batch_id: str) -> list[dict]:
        return list(self.rows)


class _FakeGateway:
    def __init__(self, *, sales: list[dict], ops: list[dict] | None = None, stock: list[dict] | None = None):
        self.sales = sales
        self.ops = ops or []
        self.stock = stock or []

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        return {"data": {"items": self.sales}}

    def fetch_open_production_orders(self) -> dict[str, Any]:
        return {"data": {"items": self.ops}}

    def fetch_stock_balances_items(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "data": {
                "items": self.stock,
                "pagination": {"total": len(self.stock)},
            }
        }


def _svc(
    *,
    sales: list[dict],
    myweg_rows: list[dict] | None = None,
    ops: list[dict] | None = None,
    stock: list[dict] | None = None,
) -> tuple[DemandService, SimpleNamespace]:
    rows = myweg_rows or [
        {
            "id": "r1",
            "line_no": 1,
            "material_weg_tratado": "M1",
            "codigo_referencia_weg": "90260001",
            "data_remessa": "2026-11-15",
            "quantidade_original_un": "1500",
            "quantidade_mi": "1.5",
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": "90260001",
                "matched_by": "code_and_reference",
            },
        }
    ]
    repo = _FakeRepo(
        {
            "id": "batch-1",
            "collection_id": "COL-E3",
            "branch": "02",
            "collected_at": "2026-11-08T08:00:00-03:00",
            "imported_at": "2026-11-08T09:00:00-03:00",
            "collection_date": "2026-11-08",
            "record_count": len(rows),
            "status": "accepted",
        },
        rows,
    )
    gateway = _FakeGateway(
        sales=sales,
        ops=ops,
        stock=stock
        if stock is not None
        else [
            {
                "product_code": "90260001",
                "quantity": 0.5,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "01",
            }
        ],
    )
    coverage = DemandCoverageService(today=TODAY)
    myweg = MyWegDemandCoveragePreviewService(
        gateway,
        myweg_source=MyWegDemandSourceService(repo),
        coverage=coverage,
        today=TODAY,
    )
    service = DemandService(
        gateway,
        coverage=coverage,
        myweg_coverage=myweg,
        today=TODAY,
        cache=_DemandSnapshotCache(0),
    )
    user = _user(
        PC_ACCESS,
        PC_DEMAND_VIEW,
        PC_MYWEG_NEEDS_VIEW,
        PC_VIEW_FILIAL_02,
    )
    return service, user


def _protheus_sale(**overrides: Any) -> dict[str, Any]:
    row = {
        "filial": "02",
        "pedido": "P1",
        "linha": "01",
        "produto": "90268888",
        "saldo": 2.0,
        "quantidade": 2.0,
        "entregue": 0.0,
        "codigo_cadastro": "000050",
        "loja_cadastro": "01",
        "nome_cliente": "OUTRO",
        "tipo_entidade": "CLIENTE",
        "unidade": "MI",
        "data_entrega": "2026-11-20",
        "no_estoque": 1.0,
    }
    row.update(overrides)
    return row


def test_e3_default_origin_protheus_compatible() -> None:
    service, user = _svc(sales=[_protheus_sale()])
    data = service.list_demand(user, branch="02")
    assert data["filters"]["origin"] == ORIGIN_PROTHEUS
    assert data["summary"]["official_aggregate"] is True
    assert all(item.get("source") == "protheus" for item in data["items"])
    assert data["myweg"] is None


def test_e3_myweg_origin_un_to_mi_and_stock_only() -> None:
    service, user = _svc(
        sales=[_protheus_sale()],
        ops=[
            {
                "filial": "02",
                "numero_op": "OP1",
                "produto": "90260001",
                "saldo_op": 9.0,
                "data_fim_prevista_op": "2026-11-14",
            }
        ],
    )
    data = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert data["filters"]["origin"] == ORIGIN_MYWEG
    assert data["summary"]["official_aggregate"] is False
    assert data["summary"]["open_quantity"] == pytest.approx(1.5)
    assert data["items"][0]["source"] == "myweg"
    assert data["items"][0]["planning"] is True
    assert data["items"][0]["covered_by_orders"] == pytest.approx(0.0)
    assert data["items"][0]["allocated_stock"] == pytest.approx(0.5)
    assert data["myweg"]["op_unit_status"] == OP_UNIT_UNVERIFIED
    assert data["myweg"]["adr_status"] == "ARCHITECTURE_DECISION_REQUIRED"
    assert data["myweg"]["batch"]["collection_id"] == "COL-E3"


def test_e3_both_single_pool_shared_product() -> None:
    service, user = _svc(
        sales=[
            _protheus_sale(
                produto="90260001",
                saldo=1.0,
                quantidade=1.0,
                no_estoque=1.0,
                data_entrega="2026-11-10",
            )
        ],
        myweg_rows=[
            {
                "id": "r1",
                "line_no": 1,
                "material_weg_tratado": "M1",
                "codigo_referencia_weg": "90260001",
                "data_remessa": "2026-11-12",
                "quantidade_original_un": "1000",
                "quantidade_mi": "1",
                "sb1_resolution": {
                    "status": "confirmed",
                    "protheus_product_code": "90260001",
                    "matched_by": "code_and_reference",
                },
            }
        ],
        stock=[],
    )
    data = service.list_demand(user, branch="02", origin=ORIGIN_BOTH, page_size=50)
    assert data["summary"]["official_aggregate"] is False
    assert data["summary"]["by_origin"] is not None
    allocated = sum(item["allocated_stock"] for item in data["items"])
    assert allocated == pytest.approx(1.0)
    sources = {item["source"] for item in data["items"]}
    assert sources == {"protheus", "myweg"}
    assert any(b.get("open_quantity_myweg") is not None for b in data["horizon"])


def test_e3_linhares_overlap_not_summed() -> None:
    service, user = _svc(
        sales=[
            _protheus_sale(
                codigo_cadastro="000001",
                loja_cadastro="09",
                nome_cliente="WEG Linhares",
                produto="90260001",
                saldo=5.0,
            )
        ],
    )
    data = service.list_demand(user, branch="02", origin=ORIGIN_BOTH)
    # Linhares Protheus fica overlap_pending — só MyWEG no consolidado.
    assert all(item["source"] == "myweg" for item in data["items"])
    assert data["myweg"]["overlap_pending_count"] == 1


def test_e3_search_linhares_by_code_store() -> None:
    service, user = _svc(
        sales=[_protheus_sale()],
        myweg_rows=[
            {
                "id": "r1",
                "line_no": 1,
                "material_weg_tratado": "M1",
                "codigo_referencia_weg": "90260001",
                "data_remessa": "2026-11-15",
                "quantidade_original_un": "1000",
                "quantidade_mi": "1",
                "sb1_resolution": {
                    "status": "confirmed",
                    "protheus_product_code": "90260001",
                    "matched_by": "code_and_reference",
                },
            }
        ],
    )
    data = service.list_demand(
        user, branch="02", origin=ORIGIN_MYWEG, search="000001"
    )
    assert data["pagination"]["total"] >= 1


def test_e3_myweg_requires_permission() -> None:
    service, _ = _svc(sales=[_protheus_sale()])
    user = _user(PC_ACCESS, PC_DEMAND_VIEW, PC_VIEW_FILIAL_02)
    with pytest.raises(PermissionError):
        service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    # both degrada a Protheus
    data = service.list_demand(user, branch="02", origin=ORIGIN_BOTH)
    assert data["filters"]["origin"] == ORIGIN_PROTHEUS
    assert data["myweg"]["myweg_skipped"] == "missing_myweg_permission"


def test_e3_myweg_blocked_on_filial_01() -> None:
    service, user = _svc(sales=[_protheus_sale(filial="01")])
    user = _user(
        PC_ACCESS,
        PC_DEMAND_VIEW,
        PC_MYWEG_NEEDS_VIEW,
        PC_VIEW_FILIAL_01,
        PC_VIEW_FILIAL_02,
    )
    with pytest.raises(InvalidBranch):
        service.list_demand(user, branch="01", origin=ORIGIN_MYWEG)
    data = service.list_demand(user, branch="01", origin=ORIGIN_BOTH)
    assert data["filters"]["origin"] == ORIGIN_PROTHEUS


def test_e3_pagination_not_preview_sample() -> None:
    rows = [
        {
            "id": f"r{i}",
            "line_no": i,
            "material_weg_tratado": f"M{i}",
            "codigo_referencia_weg": f"90260{i:03d}",
            "data_remessa": "2026-11-15",
            "quantidade_original_un": "1000",
            "quantidade_mi": "1",
            "sb1_resolution": {
                "status": "confirmed",
                "protheus_product_code": f"90260{i:03d}",
                "matched_by": "code_and_reference",
            },
        }
        for i in range(1, 26)
    ]
    stock = [
        {
            "product_code": f"90260{i:03d}",
            "quantity": 0.0,
            "unit_of_measure": "MI",
            "branch": "02",
            "warehouse": "01",
        }
        for i in range(1, 26)
    ]
    service, user = _svc(sales=[_protheus_sale()], myweg_rows=rows, stock=stock)
    page1 = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG, page=1, page_size=10)
    assert page1["pagination"]["total"] == 25
    assert len(page1["items"]) == 10
    page3 = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG, page=3, page_size=10)
    assert len(page3["items"]) == 5

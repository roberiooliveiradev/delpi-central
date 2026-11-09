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


def test_op_pendencies_use_same_both_pool_and_include_myweg_and_protheus() -> None:
    service, user = _svc(sales=[_protheus_sale()])
    payload = service.list_op_pendencies(user, branch="02")
    assert payload["requested_origin"] == ORIGIN_BOTH
    assert {item["product_code"] for item in payload["items"]} == {"90268888", "90260001"}
    protheus = next(item for item in payload["items"] if item["product_code"] == "90268888")
    myweg = next(item for item in payload["items"] if item["product_code"] == "90260001")
    assert protheus["next_uncovered_pieces"] == 1000
    assert myweg["next_uncovered_pieces"] == 1000
    assert protheus["suggested_op_date"] == "2026-11-18"
    assert myweg["suggested_op_date"] == "2026-11-13"
    assert myweg["origins"] == ["myweg"]


def test_op_pendencies_without_myweg_permission_show_only_authorized_erp() -> None:
    service, user = _svc(sales=[_protheus_sale()])
    user.permissions.discard(PC_MYWEG_NEEDS_VIEW)
    payload = service.list_op_pendencies(user, branch="02")
    assert payload["requested_origin"] == ORIGIN_PROTHEUS
    assert payload["source_status"] == "partial"
    assert [item["product_code"] for item in payload["items"]] == ["90268888"]


def _fiscal_weg_case(
    qty_un: str,
    *,
    invoice_un: str = "6",
    batch_hour: str = "04",
) -> tuple[DemandService, SimpleNamespace]:
    """Protheus SD2 0,006 MI do pedido 002792, sem confundir PV e MyWEG."""
    row = {
        "id": "r-90263918",
        "line_no": 1,
        "material_weg_tratado": "WEG-90263918",
        "codigo_referencia_weg": "90263918",
        "data_remessa": "2026-11-08",
        "quantidade_original_un": qty_un,
        "quantidade_mi": str(float(qty_un) / 1000),
        "sb1_resolution": {
            "status": "confirmed",
            "protheus_product_code": "90263918",
            "matched_by": "code_and_reference",
        },
    }
    service, user = _svc(
        sales=[],
        myweg_rows=[row],
        stock=[{
            "product_code": "90263918",
            "quantity": 0,
            "unit_of_measure": "MI",
            "branch": "02",
            "warehouse": "01",
        }],
    )
    source = service._myweg_coverage._myweg_source
    source._repository.batch["collected_at"] = f"2026-11-08T{batch_hour}:00:00-03:00"

    def fetch_fiscal(**kwargs: Any) -> dict:
        assert kwargs["branch"] == "02"
        assert kwargs["customer_code"] == "000001"
        assert kwargs["customer_store"] == "09"
        assert kwargs["product_codes"] == ["90263918"]
        return {
            "data": {
                "branch": "02",
                "customer_code": "000001",
                "customer_store": "09",
                "items": [{
                    "branch": "02",
                    "invoice_number": "017071",
                    "invoice_series": "02",
                    "item": "04",
                    "product_code": "90263918",
                    "quantity": "0.006",
                    "quantity_un": invoice_un,
                    "unit": "MI",
                    "issue_date": "2026-11-08",
                    "customer_code": "000001",
                    "customer_store": "09",
                    "situation": "emitted",
                    "is_return": False,
                    "comparable": True,
                }],
            },
        }

    service._myweg_coverage._gateway.list_customer_outbound_invoice_line_items = fetch_fiscal
    return service, user


def test_e3_full_fiscal_fifo_credit_removes_duplicate_op_pendency() -> None:
    service, user = _fiscal_weg_case("6")
    demand = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert demand["items"] == []
    assert demand["myweg"]["fiscal_reconciliation"]["applied_un"] == "6"
    assert demand["myweg"]["fiscal_reconciliation"]["recognition_status"] == (
        "weg_acknowledgment_not_proven"
    )
    pendencies = service.list_op_pendencies(user, branch="02")
    assert not any(
        item["kind"] == "include_production_order" and item["product_code"] == "90263918"
        for item in pendencies["items"]
    )


def test_e3_partial_fiscal_credit_flows_to_demand_and_op_pendencies() -> None:
    service, user = _fiscal_weg_case("11")
    demand = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    line = demand["items"][0]
    assert line["open_quantity"] == pytest.approx(0.005)
    assert line["raw_myweg_quantity_mi"] == pytest.approx(0.011)
    assert line["fiscal_offset_mi"] == pytest.approx(0.006)
    assert line["fiscal_invoice_refs"][0]["invoice"] == "017071"
    pendencies = service.list_op_pendencies(user, branch="02")
    op = next(item for item in pendencies["items"] if item["kind"] == "include_production_order")
    assert op["product_code"] == "90263918"
    assert op["next_uncovered_pieces"] == 5


def test_e3_ambiguous_fiscal_batch_does_not_suggest_unnecessary_op() -> None:
    service, user = _fiscal_weg_case("6", batch_hour="14")
    demand = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert demand["items"][0]["fiscal_coverage_incomplete"] is True
    pendencies = service.list_op_pendencies(user, branch="02")
    assert pendencies["op_count"] == 0
    assert "confira as notas" in pendencies["warning"]


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


def test_e3_myweg_90263964_real_mi_op_covers_26_un() -> None:
    """Regressão #1546: unidade C2_UM=MI, OP 0,200 MI cobre 26 peças."""
    rows = [{
        "id": "r-90263964",
        "line_no": 1,
        "material_weg_tratado": "90263964",
        "codigo_referencia_weg": "90263964",
        "data_remessa": "2026-10-28",
        "quantidade_original_un": "26",
        "quantidade_mi": "0.026",
        "sb1_resolution": {
            "status": "confirmed",
            "protheus_product_code": "90263964",
            "matched_by": "code_and_reference",
        },
    }]
    ops = [
        {
            "filial": "02",
            "numero_op": "11286701001",
            "produto": "90263964",
            "saldo_op": 0.2,
            "unidade_op": "MI",
            "unidade_produto": "MI",
            "unidade": "MI",
            "observacao_op": "Liberar primeiro lote.",
            "data_fim_prevista_op": "2026-11-09",
        },
        {
            "filial": "01",
            "numero_op": "OUTRA-FILIAL",
            "produto": "90263964",
            "saldo_op": 900,
            "unidade": "PC",
        },
    ]
    stock = [{
        "product_code": "90263964",
        "quantity": 0.0,
        "unit_of_measure": "MI",
        "branch": "02",
        "warehouse": "01",
    }]
    service, user = _svc(
        sales=[_protheus_sale()], myweg_rows=rows, ops=ops, stock=stock
    )
    payload = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    line = payload["items"][0]
    assert line["open_quantity"] == pytest.approx(0.026)
    assert line["covered_by_orders"] == pytest.approx(0.026)
    assert line["uncovered_quantity"] == pytest.approx(0.0)
    assert line["covering_orders"] == [
        {
            "production_order": "11286701001",
            "quantity": 0.026,
            "expected_date": "2026-11-09",
            "observation": "Liberar primeiro lote.",
        }
    ]
    assert line["status"] == "late"
    assert line["op_coverage_incomplete"] is False
    assert payload["myweg"]["op_coverage_complete"] is True
    assert payload["myweg"]["op_verified_count"] == 1


def test_e3_myweg_mi_not_converted_twice_and_unknown_op_flagged() -> None:
    service, user = _svc(
        sales=[_protheus_sale()],
        ops=[
            {
                "filial": "02",
                "numero_op": "OP-MI",
                "produto": "90260001",
                "saldo_op": 0.3,
                "unidade": "MI",
                "data_fim_prevista_op": "2026-11-12",
            },
            {
                "filial": "02",
                "numero_op": "OP-SEM-UM",
                "produto": "90260001",
                "saldo_op": 2.0,
            },
        ],
    )
    payload = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    line = payload["items"][0]
    assert line["allocated_stock"] == pytest.approx(0.5)
    assert line["covered_by_orders"] == pytest.approx(0.3)
    assert line["uncovered_quantity"] == pytest.approx(0.7)
    assert line["op_coverage_incomplete"] is True
    assert payload["myweg"]["op_coverage_complete"] is False
    assert payload["myweg"]["op_unit_status"] == OP_UNIT_UNVERIFIED
    assert payload["myweg"]["op_unverified_count"] == 1


def test_e3_both_mp_sales_do_not_affect_myweg_or_cross_source_coverage() -> None:
    """#1552: MP em vendas não faz overlap, estoque ou alerta indevido."""
    service, user = _svc(
        sales=[
            _protheus_sale(
                pedido="MP-001", produto="90260001", tipo_produto=" MP ",
                unidade="KG", saldo=90.0, quantidade=90.0, no_estoque=90.0,
                data_entrega="2026-11-01",
            ),
            _protheus_sale(
                pedido="PA-001", produto="90268888", tipo_produto="PA",
                saldo=2.0, quantidade=2.0, unidade="MI",
            ),
        ]
    )
    both = service.list_demand(user, branch="02", origin=ORIGIN_BOTH)
    assert {row["source"] for row in both["items"]} == {"protheus", "myweg"}
    assert {row["sales_order"] for row in both["items"]} == {"PA-001", "MyWEG"}
    assert both["myweg"]["overlap_pending_count"] == 0
    assert both["myweg"]["reconciliation_blocked_count"] == 0
    assert both["summary"]["by_origin"]["protheus"]["line_count"] == 1
    assert both["summary"]["by_origin"]["myweg"]["line_count"] == 1
    assert both["summary"]["open_quantity"] == pytest.approx(3.5)
    assert sum(bucket["open_quantity"] for bucket in both["horizon"]) == pytest.approx(3.5)

    pending = service.list_op_pendencies(user, branch="02")
    op_items = [item for item in pending["items"] if item["kind"] == "include_production_order"]
    assert {item["product_code"] for item in op_items} == {"90260001", "90268888"}
    myweg_pending = next(item for item in op_items if item["product_code"] == "90260001")
    assert myweg_pending["origins"] == ["myweg"]


def test_e3_myweg_origin_unchanged_when_sales_order_is_mp() -> None:
    """MP é excluído apenas da carteira de vendas do PCP, não do lote WEG."""
    service, user = _svc(
        sales=[_protheus_sale(
            pedido="MP-001", produto="90260001", tipo_produto="MP",
            saldo=90.0, unidade="KG",
        )]
    )
    result = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert result["pagination"]["total"] == 1
    assert result["items"][0]["source"] == "myweg"
    assert result["items"][0]["product_code"] == "90260001"


def test_e3_both_one_op_pool_no_double_allocation() -> None:
    rows = [{
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
    }]
    service, user = _svc(
        sales=[_protheus_sale(
            produto="90260001",
            saldo=1.0,
            quantidade=1.0,
            no_estoque=0.0,
            data_entrega="2026-11-10",
        )],
        myweg_rows=rows,
        stock=[],
        ops=[{
            "filial": "02",
            "numero_op": "OP-COMUM",
            "produto": "90260001",
            "saldo_op": 1.5,
            "unidade": "MI",
            "data_fim_prevista_op": "2026-11-11",
        }],
    )
    payload = service.list_demand(user, branch="02", origin=ORIGIN_BOTH)
    by_source = {item["source"]: item for item in payload["items"]}
    assert by_source["protheus"]["covered_by_orders"] == pytest.approx(1.0)
    assert by_source["myweg"]["covered_by_orders"] == pytest.approx(0.5)
    assert sum(row["covered_by_orders"] for row in payload["items"]) == pytest.approx(1.5)
    assert payload["myweg"]["op_coverage_complete"] is True


def test_e3_myweg_op_read_failure_keeps_needs_with_partial_coverage_warning() -> None:
    service, user = _svc(sales=[_protheus_sale()])
    def _op_down() -> dict:
        raise RuntimeError("source unavailable")
    service._myweg_coverage._gateway.fetch_open_production_orders = _op_down  # type: ignore[method-assign]
    payload = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["op_coverage_incomplete"] is True
    assert payload["myweg"]["op_coverage_complete"] is False
    assert payload["myweg"]["op_source_unavailable"] is True


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


def test_e3_both_degrades_to_protheus_when_myweg_fails() -> None:
    class _BoomGateway(_FakeGateway):
        def fetch_open_sales_orders(self) -> dict[str, Any]:
            raise RuntimeError("sales boom")

    sales = [_protheus_sale()]
    # DemandService Protheus path uses same gateway — need Protheus load to work
    # while MyWEG resolve fails. Fail only inside myweg resolve via broken stock+sales
    # on the coverage service by stubbing resolve.
    service, user = _svc(sales=sales)
    calls = {"n": 0}

    def _boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        calls["n"] += 1
        raise RuntimeError("myweg resolve failed")

    service._myweg_coverage.resolve_demand_origin_lines = _boom  # type: ignore[method-assign]
    data = service.list_demand(user, branch="02", origin=ORIGIN_BOTH)
    assert data["filters"]["origin"] == ORIGIN_PROTHEUS
    assert data["myweg"]["myweg_degraded"] is True
    assert data["myweg"]["myweg_skipped"] == "myweg_source_failed"
    assert data["summary"]["official_aggregate"] is True
    assert all(item["source"] == "protheus" for item in data["items"])
    assert data["pagination"]["total"] >= 1
    assert calls["n"] == 1


def test_e3_myweg_lines_remain_when_sb2_unavailable() -> None:
    service, user = _svc(
        sales=[_protheus_sale()],
        stock=[],  # produto exclusivo ausente no SB2
    )
    # Forçar erro SB2
    def _sb2_fail(**_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("sb2 down")

    service._myweg_coverage._gateway.fetch_stock_balances_items = _sb2_fail  # type: ignore[method-assign]
    data = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG)
    assert data["pagination"]["total"] == 1
    item = data["items"][0]
    assert item["source"] == "myweg"
    assert item["open_quantity"] == pytest.approx(1.5)
    assert item["allocated_stock"] == pytest.approx(0.0)
    assert item["uncovered_quantity"] == pytest.approx(1.5)
    assert data["myweg"]["pending_without_stock_source_count"] == 1
    assert data["myweg"]["stock_incomplete"] is True


def test_e3_myweg_cache_reused_across_pages() -> None:
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
        for i in range(1, 6)
    ]
    stock = [
        {
            "product_code": f"90260{i:03d}",
            "quantity": 0.0,
            "unit_of_measure": "MI",
            "branch": "02",
            "warehouse": "01",
        }
        for i in range(1, 6)
    ]
    service, user = _svc(sales=[_protheus_sale()], myweg_rows=rows, stock=stock)
    resolve_calls = {"n": 0}
    original = service._myweg_coverage.resolve_demand_origin_lines

    def _counted(*args: Any, **kwargs: Any) -> dict[str, Any]:
        resolve_calls["n"] += 1
        return original(*args, **kwargs)

    service._myweg_coverage.resolve_demand_origin_lines = _counted  # type: ignore[method-assign]
    # Cache com TTL > 0 para reutilizar entre páginas.
    service._cache = _DemandSnapshotCache(120)
    p1 = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG, page=1, page_size=2)
    p2 = service.list_demand(user, branch="02", origin=ORIGIN_MYWEG, page=2, page_size=2)
    assert p1["pagination"]["total"] == 5
    assert len(p2["items"]) == 2
    assert resolve_calls["n"] == 1

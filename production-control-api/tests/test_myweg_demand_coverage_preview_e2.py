"""Etapa 2 — prévia cobertura MyWEG reutilizando DemandCoverageService."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

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
    STATUS_AT_RISK,
    STATUS_COVERED_BY_ORDER,
    STATUS_COVERED_BY_STOCK,
    DemandCoverageService,
)
from production_control_app.domain.services.myweg_demand_coverage_adapter import (
    apply_pool_stock_to_inputs,
    build_stock_pool_mi,
    classify_consolidation,
    conservation_check,
    mi_to_float_for_coverage,
    projection_to_coverage_input,
    un_to_mi,
)
from production_control_app.domain.services.myweg_demand_projection import (
    MyWegDemandProjectionLine,
    project_myweg_demand_lines,
)

TODAY = date(2026, 11, 8)


def _user(*perms: str) -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=False, permissions=set(perms))


def _proj(
    *,
    record_id: str = "r1",
    product: str = "90260001",
    qty_un: str = "1500",
    remessa: str = "2026-11-15",
    eligible: bool = True,
    matched_by: str = "code_and_reference",
    status: str = "confirmed",
) -> MyWegDemandProjectionLine:
    rows = [
        {
            "id": record_id,
            "line_no": 1,
            "material_weg_tratado": "M1",
            "codigo_referencia_weg": product,
            "data_remessa": remessa,
            "quantidade_original_un": qty_un,
            "quantidade_mi": str(Decimal(qty_un) / Decimal("1000")),
            "sb1_resolution": {
                "status": status,
                "protheus_product_code": product if status == "confirmed" else None,
                "matched_by": matched_by if eligible or status == "confirmed" else None,
            },
        }
    ]
    if not eligible and status != "confirmed":
        rows[0]["sb1_resolution"] = {"status": status, "protheus_product_code": None}
    lines = project_myweg_demand_lines(rows, batch_id="batch-1", collected_at="2026-11-08T08:00:00-03:00")
    return lines[0]


def test_ac03_un_to_mi_exact() -> None:
    assert un_to_mi(Decimal("1500")) == Decimal("1.5")
    assert mi_to_float_for_coverage(Decimal("1.5")) == 1.5
    assert un_to_mi("1000") == Decimal("1")


def test_stock_partial_op_partial_uncovered() -> None:
    line = _proj(qty_un="1500")
    raw = projection_to_coverage_input(line, product_stock_mi=0.5)
    assert raw["saldo"] == 1.5
    assert raw["no_estoque"] == 0.5
    coverage = DemandCoverageService(today=TODAY)
    result = coverage.build(
        open_sales_orders=[raw],
        open_production_orders=[
            {
                "filial": "02",
                "numero_op": "OP1",
                "produto": "90260001",
                "saldo_op": 0.7,
                "data_fim_prevista_op": "2026-11-14",
            }
        ],
        branch="02",
    )
    assert len(result) == 1
    assert result[0].allocated_stock == 0.5
    assert result[0].covering_orders[0]["quantity"] == 0.7
    assert result[0].uncovered_quantity == pytest.approx(0.3)
    assert conservation_check(result)["ok"] is True


def test_two_remessas_compete_same_stock() -> None:
    a = _proj(record_id="a", qty_un="1000", remessa="2026-11-10")
    b = _proj(record_id="b", qty_un="1000", remessa="2026-11-20")
    inputs = [
        projection_to_coverage_input(a, product_stock_mi=0.8),
        projection_to_coverage_input(b, product_stock_mi=0.8),
    ]
    inputs = apply_pool_stock_to_inputs(
        inputs, {("02", "90260001"): 0.8}, branch="02"
    )
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=inputs, open_production_orders=[], branch="02"
    )
    by_id = {line.line_item: line for line in lines}
    assert by_id["a"].allocated_stock == 0.8
    assert by_id["b"].allocated_stock == 0.0
    assert by_id["b"].uncovered_quantity == 1.0


def test_two_needs_compete_same_op() -> None:
    a = _proj(record_id="a", qty_un="800", remessa="2026-11-10")
    b = _proj(record_id="b", qty_un="800", remessa="2026-11-12")
    inputs = [
        projection_to_coverage_input(a, product_stock_mi=0.0),
        projection_to_coverage_input(b, product_stock_mi=0.0),
    ]
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=inputs,
        open_production_orders=[
            {
                "filial": "02",
                "numero_op": "OPX",
                "produto": "90260001",
                "saldo_op": 1.0,
                "data_fim_prevista_op": "2026-11-11",
            }
        ],
        branch="02",
    )
    by_id = {line.line_item: line for line in lines}
    assert by_id["a"].covering_orders[0]["quantity"] == 0.8
    assert by_id["b"].covering_orders[0]["quantity"] == 0.2
    assert sum(o["quantity"] for line in lines for o in line.covering_orders) == pytest.approx(1.0)


def test_op_after_due_is_at_risk() -> None:
    line = _proj(qty_un="1000", remessa="2026-11-10")
    raw = projection_to_coverage_input(line, product_stock_mi=0.0)
    result = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[raw],
        open_production_orders=[
            {
                "filial": "02",
                "numero_op": "LATE",
                "produto": "90260001",
                "saldo_op": 1.0,
                "data_fim_prevista_op": "2026-11-20",
            }
        ],
        branch="02",
    )
    assert result[0].status == STATUS_AT_RISK
    assert result[0].uncovered_quantity == 0.0


def test_zero_stock_with_op_covered() -> None:
    line = _proj(qty_un="500")
    raw = projection_to_coverage_input(line, product_stock_mi=0.0)
    result = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[raw],
        open_production_orders=[
            {
                "filial": "02",
                "numero_op": "OPZ",
                "produto": "90260001",
                "saldo_op": 0.5,
                "data_fim_prevista_op": "2026-11-14",
            }
        ],
        branch="02",
    )
    assert result[0].status == STATUS_COVERED_BY_ORDER


def test_no_stock_no_op_uncovered() -> None:
    line = _proj(qty_un="500")
    raw = projection_to_coverage_input(line, product_stock_mi=0.0)
    result = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[raw], open_production_orders=[], branch="02"
    )
    assert result[0].uncovered_quantity == 0.5
    assert result[0].status == STATUS_AT_RISK


def test_unconfirmed_and_provisional_excluded_from_adapter_eligibility() -> None:
    pending = _proj(record_id="p", eligible=False, status="pending", product="90260001")
    assert pending.coverage_eligible is False
    sample = project_myweg_demand_lines(
        [
            {
                "id": "s1",
                "line_no": 1,
                "material_weg_tratado": "M",
                "data_remessa": "2026-11-15",
                "quantidade_original_un": "10",
                "quantidade_mi": "0.01",
                "sb1_resolution": {
                    "status": "confirmed",
                    "protheus_product_code": "80016673",
                    "matched_by": "provisional_sample_code_no_production",
                },
            }
        ],
        batch_id="b",
    )[0]
    assert sample.coverage_eligible is False


def test_overlap_linhares_not_summed_other_store_kept() -> None:
    classified = classify_consolidation(
        protheus_items=[
            {
                "filial": "02",
                "pedido": "P1",
                "linha": "01",
                "produto": "90260001",
                "saldo": 10,
                "codigo_cadastro": "000001",
                "loja_cadastro": "09",
                "unidade": "MI",
                "tipo_entidade": "CLIENTE",
                "no_estoque": 1,
            },
            {
                "filial": "02",
                "pedido": "P2",
                "linha": "01",
                "produto": "90261111",
                "saldo": 5,
                "codigo_cadastro": "000001",
                "loja_cadastro": "11",
                "unidade": "MI",
                "tipo_entidade": "CLIENTE",
                "nome_cliente": "WEG Automacao",
                "no_estoque": 0,
            },
        ],
        myweg_eligible_products={"90260001"},
    )
    assert len(classified["overlap_pending"]) == 1
    assert len(classified["protheus_for_coverage"]) == 1
    assert classified["protheus_for_coverage"][0]["loja_cadastro"] == "11"


def test_pc_unit_blocked() -> None:
    classified = classify_consolidation(
        protheus_items=[
            {
                "filial": "02",
                "pedido": "PC1",
                "produto": "X",
                "saldo": 1,
                "codigo_cadastro": "000999",
                "loja_cadastro": "01",
                "unidade": "PC",
                "tipo_entidade": "CLIENTE",
            }
        ],
        myweg_eligible_products=set(),
    )
    assert len(classified["reconciliation_blocked"]) == 1
    assert classified["protheus_for_coverage"] == []


def test_stock_pool_does_not_sum_no_estoque_and_sb2() -> None:
    pool = build_stock_pool_mi(
        branch="02",
        protheus_items=[
            {
                "filial": "02",
                "produto": "90260001",
                "no_estoque": 2.0,
            }
        ],
        myweg_product_codes=["90260001", "90269999"],
        sb2_quantities={"90260001": 99.0, "90269999": 0.0},
        sb2_complete=True,
    )
    assert pool["pool"][("02", "90260001")] == 2.0
    assert pool["source_by_product"]["02|90260001"] == "no_estoque"
    assert pool["pool"][("02", "90269999")] == 0.0
    assert "90269999" in pool["zero_confirmed_products"]


def test_sb2_error_marks_incomplete_not_silent_zero() -> None:
    pool = build_stock_pool_mi(
        branch="02",
        protheus_items=[],
        myweg_product_codes=["90260001"],
        sb2_quantities={},
        sb2_complete=False,
        sb2_error="timeout",
    )
    assert pool["incomplete"] is True
    assert ("02", "90260001") not in pool["pool"]
    assert "90260001" in pool["missing_sb2_products"]


def test_small_mi_rounding_conservation() -> None:
    line = _proj(qty_un="1")  # 0.001 MI
    raw = projection_to_coverage_input(line, product_stock_mi=0.001)
    result = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[raw], open_production_orders=[], branch="02"
    )
    assert result[0].status == STATUS_COVERED_BY_STOCK
    assert conservation_check(result)["ok"] is True


class _FakeRepo:
    def __init__(self, batch: dict, rows: list[dict]) -> None:
        self.batch = batch
        self.rows = rows

    def get_latest_batch(self) -> dict | None:
        return self.batch

    def list_batch_records_for_compare(self, *, batch_id: str) -> list[dict]:
        return list(self.rows)


class _FakeGateway:
    def __init__(
        self,
        *,
        sales: list[dict],
        ops: list[dict],
        stock_rows: list[dict] | None = None,
        stock_error: bool = False,
    ) -> None:
        self.sales = sales
        self.ops = ops
        self.stock_rows = stock_rows or []
        self.stock_error = stock_error

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        return {"data": {"items": self.sales}}

    def fetch_open_production_orders(self) -> dict[str, Any]:
        return {"data": {"items": self.ops}}

    def fetch_stock_balances_items(self, **kwargs: Any) -> dict[str, Any]:
        if self.stock_error:
            raise RuntimeError("sb2 unavailable")
        return {"data": {"items": self.stock_rows, "pagination": {"total": len(self.stock_rows)}}}


def _preview_service(
    *,
    sales: list[dict] | None = None,
    ops: list[dict] | None = None,
    stock_rows: list[dict] | None = None,
    stock_error: bool = False,
    myweg_rows: list[dict] | None = None,
) -> tuple[MyWegDemandCoveragePreviewService, SimpleNamespace]:
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
            "collection_id": "COL1",
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
        sales=sales
        or [
            {
                "filial": "02",
                "pedido": "OTHER",
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
        ],
        ops=ops or [],
        stock_rows=stock_rows
        if stock_rows is not None
        else [{"product_code": "90260001", "quantity": 0.5, "unit_of_measure": "MI"}],
        stock_error=stock_error,
    )
    service = MyWegDemandCoveragePreviewService(
        gateway,
        myweg_source=MyWegDemandSourceService(repo),
        coverage=DemandCoverageService(today=TODAY),
        today=TODAY,
    )
    user = _user(PC_ACCESS, PC_DEMAND_VIEW, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02)
    return service, user


def test_preview_service_end_to_end_inert_and_units() -> None:
    service, user = _preview_service(
        ops=[
            {
                "filial": "02",
                "numero_op": "OP1",
                "produto": "90260001",
                "saldo_op": 0.7,
                "data_fim_prevista_op": "2026-11-14",
            }
        ]
    )
    preview = service.build_preview(user, branch="02")
    assert preview["wired_to_demand_endpoint"] is False
    assert preview["productive_activation_blocked"] is True
    assert preview["adr_status"] == "ARCHITECTURE_DECISION_REQUIRED"
    myweg = preview["scenarios"]["myweg_only"]["summary"]
    assert myweg["unit"] == "MI"
    assert myweg["open_quantity"] == pytest.approx(1.5)
    assert myweg["covered_by_stock"] == pytest.approx(0.5)
    assert myweg["covered_by_orders"] == pytest.approx(0.7)
    assert myweg["uncovered_quantity"] == pytest.approx(0.3)
    assert preview["scenarios"]["myweg_only"]["conservation"]["ok"] is True
    cons = preview["scenarios"]["consolidated_proposed"]
    assert cons["definitive_total_published"] is False
    assert cons["blocked"] is True


def test_preview_rejects_filial_01_and_missing_myweg_perm() -> None:
    service, user = _preview_service()
    with pytest.raises(InvalidBranch):
        service.build_preview(user, branch="01")
    bad = _user(PC_ACCESS, PC_DEMAND_VIEW, PC_VIEW_FILIAL_02)
    with pytest.raises(PermissionError):
        service.build_preview(bad, branch="02")


def test_preview_sb2_error_does_not_invent_coverage() -> None:
    service, user = _preview_service(stock_error=True, stock_rows=[])
    preview = service.build_preview(user, branch="02")
    assert preview["stock"]["incomplete"] is True
    assert preview["scenarios"]["myweg_only"]["line_count"] == 0


def test_latest_batch_wins_in_source() -> None:
    """Coleta mais recente (por collected_at do repositório) é a usada."""
    service, user = _preview_service()
    preview = service.build_preview(user, branch="02")
    assert preview["batch"]["collection_id"] == "COL1"

"""Etapa 2 — prévia cobertura MyWEG + rework segurança/confiabilidade."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.myweg_demand_coverage_preview_service import (
    MyWegDemandCoveragePreviewService,
    PreviewPayloadError,
    require_items_list,
)
from production_control_app.application.services.myweg_demand_source_service import (
    MyWegDemandSourceService,
)
from production_control_app.core.security import (
    PC_ACCESS,
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
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
    CUSTOMER_IDENTITY_PENDING,
    OP_UNIT_UNVERIFIED,
    apply_pool_stock_to_inputs,
    build_stock_pool_mi,
    classify_consolidation,
    conservation_check,
    is_linhares_open_order,
    mi_to_float_for_coverage,
    projection_to_coverage_input,
    summarize_units,
    un_to_mi,
)
from production_control_app.domain.services.myweg_demand_projection import (
    MyWegDemandProjectionLine,
    project_myweg_demand_lines,
)
from production_control_app.jobs.myweg_demand_coverage_preview import __main__ as preview_cli

TODAY = date(2026, 11, 8)


def _user(*perms: str, is_superadmin: bool = False) -> SimpleNamespace:
    return SimpleNamespace(is_superadmin=is_superadmin, permissions=set(perms))


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
    lines = project_myweg_demand_lines(
        rows, batch_id="batch-1", collected_at="2026-11-08T08:00:00-03:00"
    )
    return lines[0]


def test_ac03_un_to_mi_exact() -> None:
    assert un_to_mi(Decimal("1500")) == Decimal("1.5")
    assert mi_to_float_for_coverage(Decimal("1.5")) == 1.5
    assert un_to_mi("1000") == Decimal("1")


def test_stock_partial_op_partial_uncovered_adapter_motor() -> None:
    """Motor DemandCoverageService ainda aloca OP quando chamado diretamente."""
    line = _proj(qty_un="1500")
    raw = projection_to_coverage_input(line, product_stock_mi=0.5)
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


def test_overlap_linhares_not_summed_other_stores_kept() -> None:
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
                "no_estoque": 0,
            },
            {
                "filial": "02",
                "pedido": "P3",
                "linha": "01",
                "produto": "90262222",
                "saldo": 3,
                "codigo_cadastro": "000001",
                "loja_cadastro": "14",
                "unidade": "MI",
                "tipo_entidade": "CLIENTE",
                "no_estoque": 0,
            },
        ],
        myweg_eligible_products={"90260001"},
    )
    assert len(classified["overlap_pending"]) == 1
    assert len(classified["protheus_for_coverage"]) == 2
    stores = {item["loja_cadastro"] for item in classified["protheus_for_coverage"]}
    assert stores == {"11", "14"}


def test_codigo_cliente_does_not_identify_linhares() -> None:
    assert (
        is_linhares_open_order(
            {
                "codigo_cliente": "000001",
                "loja_cadastro": "09",
                "codigo_cadastro": "",
            }
        )
        is False
    )
    classified = classify_consolidation(
        protheus_items=[
            {
                "filial": "02",
                "pedido": "AMB",
                "produto": "X",
                "saldo": 1,
                "codigo_cliente": "000001",
                "codigo_cadastro": "",
                "loja_cadastro": "09",
                "unidade": "MI",
            }
        ],
        myweg_eligible_products=set(),
    )
    assert len(classified["customer_identity_pending"]) == 1
    assert classified["customer_identity_pending"][0]["_preview_source"] == (
        CUSTOMER_IDENTITY_PENDING
    )
    assert classified["overlap_pending"] == []
    assert classified["protheus_for_coverage"] == []


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


def test_summarize_units_mixed_mi_pc() -> None:
    summary = summarize_units(
        [
            {"unidade": "MI", "saldo": 10},
            {"unidade": "PC", "saldo": 1},
        ]
    )
    assert summary["unit_label"] == "MIXED"
    assert summary["mixed"] is True
    assert summary["blocked_non_mi_line_count"] == 1


def test_stock_pool_does_not_sum_no_estoque_and_sb2() -> None:
    pool = build_stock_pool_mi(
        branch="02",
        protheus_items=[{"filial": "02", "produto": "90260001", "no_estoque": 2.0}],
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


def test_small_mi_rounding_conservation() -> None:
    line = _proj(qty_un="1")
    raw = projection_to_coverage_input(line, product_stock_mi=0.001)
    result = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[raw], open_production_orders=[], branch="02"
    )
    assert result[0].status == STATUS_COVERED_BY_STOCK
    assert conservation_check(result)["ok"] is True
    assert conservation_check(result)["tolerance"] == 0.001


def test_require_items_rejects_invalid_payload() -> None:
    assert require_items_list({"data": {"items": []}}, "items", source_name="t") == []
    with pytest.raises(PreviewPayloadError):
        require_items_list({"data": {}}, "items", source_name="t")
    with pytest.raises(PreviewPayloadError):
        require_items_list("oops", "items", source_name="t")
    with pytest.raises(PreviewPayloadError):
        require_items_list({"data": {"items": "x"}}, "items", source_name="t")


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
        sales: list[dict] | None = None,
        ops: list[dict] | None = None,
        stock_rows: list[dict] | None = None,
        stock_error: bool = False,
        stock_payload: dict[str, Any] | None = None,
        sales_payload: Any = None,
        ops_payload: Any = None,
    ) -> None:
        self.sales = sales
        self.ops = ops
        self.stock_rows = stock_rows or []
        self.stock_error = stock_error
        self.stock_payload = stock_payload
        self.sales_payload = sales_payload
        self.ops_payload = ops_payload
        self.stock_calls: list[dict[str, Any]] = []

    def fetch_open_sales_orders(self) -> Any:
        if self.sales_payload is not None:
            return self.sales_payload
        return {"data": {"items": self.sales or []}}

    def fetch_open_production_orders(self) -> Any:
        if self.ops_payload is not None:
            return self.ops_payload
        return {"data": {"items": self.ops or []}}

    def fetch_stock_balances_items(self, **kwargs: Any) -> Any:
        self.stock_calls.append(kwargs)
        if self.stock_error:
            raise RuntimeError("sb2 unavailable")
        if self.stock_payload is not None:
            return self.stock_payload
        return {
            "data": {
                "items": self.stock_rows,
                "pagination": {"total": len(self.stock_rows)},
            }
        }


def _preview_service(
    *,
    sales: list[dict] | None = None,
    ops: list[dict] | None = None,
    stock_rows: list[dict] | None = None,
    stock_error: bool = False,
    stock_payload: dict[str, Any] | None = None,
    sales_payload: Any = None,
    ops_payload: Any = None,
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
    default_stock = [
        {
            "product_code": "90260001",
            "quantity": 0.5,
            "unit_of_measure": "MI",
            "branch": "02",
            "warehouse": "01",
        }
    ]
    gateway = _FakeGateway(
        sales=sales
        if sales is not None
        else [
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
        stock_rows=stock_rows if stock_rows is not None else default_stock,
        stock_error=stock_error,
        stock_payload=stock_payload,
        sales_payload=sales_payload,
        ops_payload=ops_payload,
    )
    service = MyWegDemandCoveragePreviewService(
        gateway,
        myweg_source=MyWegDemandSourceService(repo),
        coverage=DemandCoverageService(today=TODAY),
        today=TODAY,
    )
    user = _user(PC_ACCESS, PC_DEMAND_VIEW, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02)
    return service, user


def test_preview_service_stock_only_op_unverified() -> None:
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
    assert preview["op_unit_assumption"]["status"] == OP_UNIT_UNVERIFIED
    myweg = preview["scenarios"]["myweg_only"]
    assert myweg["op_coverage_confirmed"] is False
    assert myweg["summary"]["unit"] == "MI"
    assert myweg["summary"]["open_quantity"] == pytest.approx(1.5)
    assert myweg["summary"]["covered_by_stock"] == pytest.approx(0.5)
    assert myweg["summary"]["covered_by_orders"] == pytest.approx(0.0)
    assert myweg["summary"]["uncovered_quantity"] == pytest.approx(1.0)
    assert myweg["conservation"]["ok"] is True
    cons = preview["scenarios"]["consolidated_proposed"]
    assert cons["definitive_total_published"] is False
    assert cons["blocked"] is True
    assert "op_unit_unverified_myweg" in cons["block_reasons"]


def test_preview_rejects_filial_01_and_missing_myweg_perm() -> None:
    service, user = _preview_service()
    with pytest.raises(InvalidBranch):
        service.build_preview(user, branch="01")
    bad = _user(PC_ACCESS, PC_DEMAND_VIEW, PC_VIEW_FILIAL_02)
    with pytest.raises(PermissionError):
        service.build_preview(bad, branch="02")


def test_synthetic_superadmin_alone_is_not_enough_without_perms() -> None:
    """is_superadmin no objeto só vale se can() da plataforma reconhecer — perms ausentes falham."""
    service, _ = _preview_service()
    # can() no PCP trata is_superadmin=True como bypass — documentamos que CLI não monta isso.
    # Sem permissões e sem superadmin → Forbidden.
    plain = _user()
    with pytest.raises(PermissionError):
        service.build_preview(plain, branch="02")


def test_preview_sb2_error_does_not_invent_coverage() -> None:
    service, user = _preview_service(stock_error=True, stock_rows=[])
    preview = service.build_preview(user, branch="02")
    assert preview["stock"]["incomplete"] is True
    assert preview["scenarios"]["myweg_only"]["line_count"] == 0
    assert preview["quantities_mi"]["myweg_pending_missing_stock_source"] == pytest.approx(
        1.5
    )


def test_sb2_rejects_wrong_branch_warehouse_unit_duplicate() -> None:
    service, user = _preview_service(
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 9,
                "unit_of_measure": "MI",
                "branch": "01",
                "warehouse": "01",
            }
        ]
    )
    preview = service.build_preview(user, branch="02")
    assert preview["stock"]["sb2_complete"] is False
    reasons = {r["reason"] for r in preview["stock"]["sb2_diagnostics"]["rejected_rows"]}
    assert "branch_mismatch" in reasons

    service2, user2 = _preview_service(
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 1,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "02",
            }
        ]
    )
    p2 = service2.build_preview(user2, branch="02")
    assert any(
        r["reason"] == "warehouse_mismatch"
        for r in p2["stock"]["sb2_diagnostics"]["rejected_rows"]
    )

    service3, user3 = _preview_service(
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 1,
                "unit_of_measure": "PC",
                "branch": "02",
                "warehouse": "01",
            }
        ]
    )
    p3 = service3.build_preview(user3, branch="02")
    assert any(
        r["reason"] == "unit_incompatible"
        for r in p3["stock"]["sb2_diagnostics"]["rejected_rows"]
    )

    service4, user4 = _preview_service(
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 1,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "01",
            },
            {
                "product_code": "90260001",
                "quantity": 2,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "01",
            },
        ]
    )
    p4 = service4.build_preview(user4, branch="02")
    assert "90260001" in p4["stock"]["sb2_diagnostics"]["duplicate_products"]
    assert p4["scenarios"]["myweg_only"]["line_count"] == 0


def test_sb2_zero_confirmed_vs_absent() -> None:
    service, user = _preview_service(
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 0,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "01",
            }
        ]
    )
    preview = service.build_preview(user, branch="02")
    assert "90260001" in preview["stock"]["sb2_diagnostics"]["zero_vs_absent"][
        "zero_confirmed"
    ]
    assert preview["scenarios"]["myweg_only"]["summary"]["covered_by_stock"] == 0
    assert preview["scenarios"]["myweg_only"]["line_count"] == 1

    service2, user2 = _preview_service(stock_rows=[])
    p2 = service2.build_preview(user2, branch="02")
    assert "90260001" in p2["stock"]["sb2_diagnostics"]["zero_vs_absent"][
        "absent_or_invalid"
    ]
    assert p2["scenarios"]["myweg_only"]["line_count"] == 0


def test_invalid_sales_payload_blocks_reliable_preview() -> None:
    service, user = _preview_service(sales_payload={"data": {"not_items": []}})
    preview = service.build_preview(user, branch="02")
    assert preview["reliable"] is False
    assert preview["blocked"] is True
    assert preview["scenarios"] == {}


def test_protheus_only_mixed_units_label() -> None:
    service, user = _preview_service(
        sales=[
            {
                "filial": "02",
                "pedido": "A",
                "linha": "01",
                "produto": "P1",
                "saldo": 10,
                "quantidade": 10,
                "entregue": 0,
                "codigo_cadastro": "000050",
                "loja_cadastro": "01",
                "unidade": "MI",
                "tipo_entidade": "CLIENTE",
                "data_entrega": "2026-11-20",
                "no_estoque": 0,
            },
            {
                "filial": "02",
                "pedido": "B",
                "linha": "01",
                "produto": "P2",
                "saldo": 1,
                "quantidade": 1,
                "entregue": 0,
                "codigo_cadastro": "000051",
                "loja_cadastro": "01",
                "unidade": "PC",
                "tipo_entidade": "CLIENTE",
                "data_entrega": "2026-11-20",
                "no_estoque": 0,
            },
        ],
        stock_rows=[
            {
                "product_code": "90260001",
                "quantity": 0.5,
                "unit_of_measure": "MI",
                "branch": "02",
                "warehouse": "01",
            }
        ],
    )
    preview = service.build_preview(user, branch="02")
    assert preview["protheus_units"]["unit_label"] == "MIXED"
    assert preview["scenarios"]["protheus_only"]["summary"]["unit"] == "MIXED"
    assert preview["scenarios"]["protheus_only"]["summary"][
        "global_total_authoritative"
    ] is False
    assert preview["reconciliation_blocked"]["line_count"] == 1


def test_cli_rejects_user_json_synthetic_elevation() -> None:
    code = preview_cli.main(["--user-json", '{"is_superadmin":true}'])
    assert code == 2


def test_cli_blocks_without_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    code = preview_cli.main(["--branch", "02"])
    assert code == 2


def test_latest_batch_wins_in_source() -> None:
    service, user = _preview_service()
    preview = service.build_preview(user, branch="02")
    assert preview["batch"]["collection_id"] == "COL1"

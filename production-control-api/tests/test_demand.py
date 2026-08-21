from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from production_control_app.application.services.demand_service import (
    DemandService,
    _DemandSnapshotCache,
)
from production_control_app.domain.errors import BranchAccessDenied, InvalidBranch
from production_control_app.domain.services.demand_coverage_service import (
    STATUS_AT_RISK,
    STATUS_COVERED_BY_ORDER,
    STATUS_COVERED_BY_STOCK,
    STATUS_LATE,
    DemandCoverageService,
)

TODAY = date(2026, 8, 21)

FULL_PERMS = (
    "production-control.access",
    "production-control.demand.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _user(*permissions: str, superadmin: bool = False):
    return SimpleNamespace(is_superadmin=superadmin, permissions=list(permissions))


def _line(**overrides: Any) -> dict[str, Any]:
    row = {
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
        "preco_venda": 12.5,
        "valor_aberto": 750.0,
    }
    row.update(overrides)
    return row


def _op(**overrides: Any) -> dict[str, Any]:
    row = {
        "filial": "01",
        "numero_op": "10840401001",
        "produto": "90262910",
        "descricao_produto": "CHICOTE",
        "tipo_produto": "PA",
        "quantidade_op": 100.0,
        "quantidade_produzida": 0.0,
        "saldo_op": 100.0,
        "data_emissao_op": "2026-08-01",
        "data_inicio_prevista_op": "2026-08-10",
        "data_fim_prevista_op": "2026-08-23",
        "armazem": "01",
        "observacao_op": "",
    }
    row.update(overrides)
    return row


class FakeDemandGateway:
    def __init__(
        self,
        sales_orders: list[dict[str, Any]] | None = None,
        production_orders: list[dict[str, Any]] | None = None,
    ) -> None:
        self.sales_orders = sales_orders if sales_orders is not None else [_line()]
        self.production_orders = production_orders if production_orders is not None else []
        self.calls = 0

    def fetch_open_sales_orders(self) -> dict[str, Any]:
        self.calls += 1
        return {"data": {"items": self.sales_orders, "summary": {}}}

    def fetch_open_production_orders(self) -> dict[str, Any]:
        return {"data": {"items": self.production_orders, "resumo": []}}


def _service(gateway: FakeDemandGateway) -> DemandService:
    return DemandService(
        gateway,
        today=TODAY,
        coverage=DemandCoverageService(today=TODAY),
        cache=_DemandSnapshotCache(0),
    )


# ------------------------------------------------------------------ cobertura


def test_stock_covers_lines_in_delivery_order() -> None:
    rows = [
        _line(pedido="A", linha="01", saldo=30.0, data_entrega="2026-08-25", no_estoque=50.0),
        _line(pedido="B", linha="01", saldo=40.0, data_entrega="2026-08-28", no_estoque=50.0),
    ]
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=rows, open_production_orders=[]
    )
    first = next(line for line in lines if line.sales_order == "A")
    second = next(line for line in lines if line.sales_order == "B")

    assert first.allocated_stock == 30.0
    assert first.uncovered_quantity == 0.0
    assert first.status == STATUS_COVERED_BY_STOCK
    # Só sobraram 20 do estoque para a segunda linha.
    assert second.allocated_stock == 20.0
    assert second.uncovered_quantity == 20.0
    assert second.status == STATUS_AT_RISK


def test_supplier_sales_orders_are_excluded() -> None:
    """Remessa / venda para fornecedor (ex.: TRAMAR) não entra na demanda do PCP."""
    rows = [
        _line(pedido="CLI", nome_cliente="CLIENTE A", tipo_entidade="CLIENTE"),
        _line(
            pedido="FOR",
            nome_cliente="TRAMAR",
            tipo_entidade="FORNECEDOR",
            saldo=80.0,
            produto="90262575",
        ),
    ]
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=rows, open_production_orders=[]
    )
    assert [line.sales_order for line in lines] == ["CLI"]


def test_open_production_orders_cover_what_stock_does_not() -> None:
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[_line(saldo=60.0, no_estoque=10.0)],
        open_production_orders=[_op(saldo_op=80.0, data_fim_prevista_op="2026-08-24")],
    )
    line = lines[0]

    assert line.allocated_stock == 10.0
    assert line.uncovered_quantity == 0.0
    assert line.covering_orders == [
        {
            "production_order": "10840401001",
            "quantity": 50.0,
            "expected_date": "2026-08-24",
        }
    ]
    # OP termina depois da entrega prometida (25/08 > 24/08): compromisso mantido.
    assert line.status == STATUS_COVERED_BY_ORDER


def test_order_finishing_after_due_date_keeps_line_at_risk() -> None:
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[_line(saldo=60.0, no_estoque=0.0, data_entrega="2026-08-25")],
        open_production_orders=[_op(saldo_op=60.0, data_fim_prevista_op="2026-09-10")],
    )
    assert lines[0].status == STATUS_AT_RISK


def test_float_residual_does_not_poison_coverage_with_later_op() -> None:
    """0,75 − 0,6 − 0,15 deixa residual float; a OP seguinte não pode marcar at_risk."""
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[
            _line(
                pedido="002563",
                linha="03",
                produto="90480116",
                saldo=0.75,
                no_estoque=0.0,
                data_entrega="2026-08-28",
            )
        ],
        open_production_orders=[
            _op(
                numero_op="10656801001",
                produto="90480116",
                saldo_op=0.6,
                data_fim_prevista_op="2026-08-21",
            ),
            _op(
                numero_op="10699801001",
                produto="90480116",
                saldo_op=0.15,
                data_fim_prevista_op="2026-08-21",
            ),
            _op(
                numero_op="10705601001",
                produto="90480116",
                saldo_op=0.9,
                data_fim_prevista_op="2026-09-03",
            ),
        ],
    )
    line = lines[0]
    assert line.uncovered_quantity == 0.0
    covered = sum(float(order["quantity"]) for order in line.covering_orders)
    assert abs(covered - 0.75) < 1e-9
    assert all(order["quantity"] > 0 for order in line.covering_orders)
    assert "10705601001" not in {order["production_order"] for order in line.covering_orders}
    assert line.coverage_date == date(2026, 8, 21)
    assert line.status == STATUS_COVERED_BY_ORDER


def test_past_due_date_is_late_regardless_of_coverage() -> None:
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[_line(data_entrega="2026-08-10", no_estoque=500.0)],
        open_production_orders=[],
    )
    assert lines[0].status == STATUS_LATE
    assert lines[0].days_late(TODAY) == 11


def test_supply_is_not_reused_between_lines() -> None:
    rows = [
        _line(pedido="A", linha="01", saldo=70.0, data_entrega="2026-08-25", no_estoque=0.0),
        _line(pedido="B", linha="01", saldo=70.0, data_entrega="2026-08-26", no_estoque=0.0),
    ]
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=rows,
        open_production_orders=[_op(saldo_op=100.0)],
    )
    first = next(line for line in lines if line.sales_order == "A")
    second = next(line for line in lines if line.sales_order == "B")

    assert first.uncovered_quantity == 0.0
    assert second.uncovered_quantity == 40.0


def test_lines_without_open_balance_are_dropped() -> None:
    lines = DemandCoverageService(today=TODAY).build(
        open_sales_orders=[_line(saldo=0.0), _line(pedido="B", saldo=5.0)],
        open_production_orders=[],
    )
    assert [line.sales_order for line in lines] == ["B"]


# --------------------------------------------------------------------- rota


def test_payload_has_no_financial_fields() -> None:
    payload = _service(FakeDemandGateway()).list_demand(_user(*FULL_PERMS), branch="01")
    item = payload["items"][0]

    assert "preco_venda" not in item
    assert "valor_aberto" not in item
    assert not any("price" in key or "value" in key or "amount" in key for key in item)
    assert item["open_quantity"] == 60.0


def test_branch_filter_and_summary() -> None:
    gateway = FakeDemandGateway(
        [
            _line(filial="01", pedido="A", saldo=10.0, data_entrega="2026-08-10"),
            _line(filial="02", pedido="B", saldo=99.0),
        ]
    )
    payload = _service(gateway).list_demand(_user(*FULL_PERMS), branch="01")

    assert [item["sales_order"] for item in payload["items"]] == ["A"]
    assert payload["summary"]["line_count"] == 1
    assert payload["summary"]["open_quantity"] == 10.0
    assert payload["summary"]["late_line_count"] == 1


def test_search_matches_customer_order_and_product() -> None:
    gateway = FakeDemandGateway(
        [
            _line(pedido="A", produto="90262910"),
            _line(pedido="B", produto="80111222", nome_cliente="OUTRO"),
        ]
    )
    service = _service(gateway)
    user = _user(*FULL_PERMS)

    assert len(service.list_demand(user, branch="01", search="8011")["items"]) == 1
    assert len(service.list_demand(user, branch="01", search="outro")["items"]) == 1
    assert len(service.list_demand(user, branch="01", search="")["items"]) == 2


def test_status_and_due_window_filters() -> None:
    gateway = FakeDemandGateway(
        [
            _line(pedido="A", data_entrega="2026-08-10"),
            _line(pedido="B", data_entrega="2026-09-30", no_estoque=999.0),
        ]
    )
    service = _service(gateway)
    user = _user(*FULL_PERMS)

    late = service.list_demand(user, branch="01", status=STATUS_LATE)
    assert [item["sales_order"] for item in late["items"]] == ["A"]

    window = service.list_demand(user, branch="01", due_from="2026-09-01", due_to="2026-10-01")
    assert [item["sales_order"] for item in window["items"]] == ["B"]


def test_pagination_and_sorting() -> None:
    rows = [
        _line(pedido=f"P{index}", data_entrega=f"2026-09-0{index}", saldo=float(index))
        for index in range(1, 6)
    ]
    service = _service(FakeDemandGateway(rows))
    user = _user(*FULL_PERMS)

    first = service.list_demand(user, branch="01", page=1, page_size=2)
    assert [item["sales_order"] for item in first["items"]] == ["P1", "P2"]
    assert first["pagination"]["total"] == 5
    assert first["pagination"]["total_pages"] == 3
    assert first["pagination"]["is_complete"] is False

    desc = service.list_demand(user, branch="01", sort="open_quantity", direction="desc", page_size=1)
    assert desc["items"][0]["sales_order"] == "P5"


def test_horizon_groups_by_delivery_week_with_late_bucket() -> None:
    gateway = FakeDemandGateway(
        [
            _line(pedido="A", data_entrega="2026-08-10", saldo=5.0),
            _line(pedido="B", data_entrega="2026-08-25", saldo=7.0),
            _line(pedido="C", data_entrega="2026-08-27", saldo=3.0),
        ]
    )
    horizon = _service(gateway).list_demand(_user(*FULL_PERMS), branch="01")["horizon"]

    assert horizon[0]["key"] == "late"
    assert horizon[0]["open_quantity"] == 5.0
    # 25 e 27/08 caem na mesma semana (segunda 24/08).
    assert horizon[1]["start_date"] == "2026-08-24"
    assert horizon[1]["open_quantity"] == 10.0


def test_cache_avoids_refetching_and_refresh_forces_reload() -> None:
    gateway = FakeDemandGateway()
    service = DemandService(
        gateway,
        today=TODAY,
        coverage=DemandCoverageService(today=TODAY),
        cache=_DemandSnapshotCache(300),
    )
    user = _user(*FULL_PERMS)

    service.list_demand(user, branch="01")
    service.list_demand(user, branch="01", page=2)
    assert gateway.calls == 1

    service.list_demand(user, branch="01", refresh=True)
    assert gateway.calls == 2


# --------------------------------------------------------------- permissões


def test_requires_demand_permission() -> None:
    service = _service(FakeDemandGateway())
    user = _user("production-control.access", "production-control.view.filial-01")
    with pytest.raises(PermissionError):
        service.list_demand(user, branch="01")


def test_requires_branch_permission() -> None:
    service = _service(FakeDemandGateway())
    user = _user(
        "production-control.access",
        "production-control.demand.view",
        "production-control.view.filial-01",
    )
    with pytest.raises(BranchAccessDenied):
        service.list_demand(user, branch="02")


def test_rejects_unknown_branch() -> None:
    service = _service(FakeDemandGateway())
    with pytest.raises(InvalidBranch):
        service.list_demand(_user(*FULL_PERMS), branch="09")

"""Checklist «a faturar até hoje» — estoque amarelo / faturado verde."""

from __future__ import annotations

from datetime import date

from production_control_app.domain.services.billing_due_today_service import (
    CHECK_INVOICED,
    CHECK_PENDING,
    CHECK_STOCK,
    BillingDueTodayService,
)


TODAY = date(2026, 8, 21)


def _open(
    *,
    pedido: str,
    linha: str,
    produto: str,
    saldo: float,
    estoque: float,
    entrega: str,
    cliente: str = "ACME",
    codigo: str = "C001",
    filial: str = "01",
) -> dict:
    return {
        "filial": filial,
        "pedido": pedido,
        "linha": linha,
        "produto": produto,
        "nome_cliente": cliente,
        "codigo_cadastro": codigo,
        "loja_cadastro": "01",
        "saldo": saldo,
        "quantidade": saldo,
        "entregue": 0,
        "data_entrega": entrega,
        "no_estoque": estoque,
    }


def _closed(
    *,
    pedido: str,
    linha: str,
    produto: str,
    faturamento: str,
    entrega: str | None = None,
    cliente: str = "ACME",
    codigo: str = "C001",
    filial: str = "01",
) -> dict:
    return {
        "filial": filial,
        "pedido": pedido,
        "linha": linha,
        "produto": produto,
        "nome_cliente": cliente,
        "codigo_cadastro": codigo,
        "loja_cadastro": "01",
        "saldo": 0,
        "quantidade": 10,
        "entregue": 10,
        "data_entrega": entrega,
        "data_faturamento": faturamento,
        "no_estoque": 0,
    }


def test_billing_due_today_marks_stock_and_pending() -> None:
    service = BillingDueTodayService(today=TODAY)
    payload = service.build(
        open_sales_orders=[
            _open(
                pedido="PV1",
                linha="01",
                produto="9001",
                saldo=5,
                estoque=10,
                entrega="2026-08-21",
            ),
            _open(
                pedido="PV1",
                linha="02",
                produto="9002",
                saldo=3,
                estoque=0,
                entrega="2026-08-20",
            ),
            _open(
                pedido="PV2",
                linha="01",
                produto="9003",
                saldo=1,
                estoque=1,
                entrega="2026-08-30",
            ),
        ],
        recently_closed_orders=[],
        branch="01",
    )

    assert payload["line_count"] == 2
    assert payload["stock_count"] == 1
    assert payload["pending_count"] == 1
    assert payload["invoiced_count"] == 0
    assert len(payload["customers"]) == 1
    checks = {line["product_code"]: line["check"] for line in payload["customers"][0]["lines"]}
    assert checks == {"9001": CHECK_STOCK, "9002": CHECK_PENDING}


def test_billing_due_today_includes_invoiced_green() -> None:
    service = BillingDueTodayService(today=TODAY)
    payload = service.build(
        open_sales_orders=[
            _open(
                pedido="PV1",
                linha="01",
                produto="9001",
                saldo=2,
                estoque=0,
                entrega="2026-08-21",
                cliente="Beta",
                codigo="C002",
            )
        ],
        recently_closed_orders=[
            _closed(
                pedido="PV9",
                linha="01",
                produto="9009",
                faturamento="2026-08-21",
                entrega="2026-08-20",
                cliente="ACME",
                codigo="C001",
            ),
            # Entrega futura — fora do card mesmo faturado hoje.
            _closed(
                pedido="PV8",
                linha="01",
                produto="9008",
                faturamento="2026-08-21",
                entrega="2026-09-01",
            ),
            # Faturado ontem — fora.
            _closed(
                pedido="PV7",
                linha="01",
                produto="9007",
                faturamento="2026-08-20",
                entrega="2026-08-20",
            ),
        ],
        branch="01",
    )

    assert payload["line_count"] == 2
    assert payload["invoiced_count"] == 1
    assert payload["pending_count"] == 1
    by_product = {
        line["product_code"]: line["check"]
        for customer in payload["customers"]
        for line in customer["lines"]
    }
    assert by_product["9009"] == CHECK_INVOICED
    assert by_product["9001"] == CHECK_PENDING
    assert "9008" not in by_product
    assert "9007" not in by_product


def test_billing_due_today_excludes_supplier_entity() -> None:
    service = BillingDueTodayService(today=TODAY)
    payload = service.build(
        open_sales_orders=[
            _open(
                pedido="FOR",
                linha="01",
                produto="9001",
                saldo=5,
                estoque=10,
                entrega="2026-08-21",
                cliente="TRAMAR",
            )
            | {"tipo_entidade": "FORNECEDOR"},
            _open(
                pedido="CLI",
                linha="01",
                produto="9002",
                saldo=2,
                estoque=0,
                entrega="2026-08-21",
                cliente="ACME",
            )
            | {"tipo_entidade": "CLIENTE"},
        ],
        recently_closed_orders=[],
        branch="01",
    )
    assert payload["line_count"] == 1
    assert payload["customers"][0]["customer_name"] == "ACME"


def test_billing_due_today_fifo_stock_across_lines() -> None:
    """Estoque do produto é compartilhado — quem vence antes consome primeiro."""
    service = BillingDueTodayService(today=TODAY)
    payload = service.build(
        open_sales_orders=[
            _open(
                pedido="A",
                linha="01",
                produto="P1",
                saldo=4,
                estoque=5,
                entrega="2026-08-19",
                cliente="Z",
                codigo="CZ",
            ),
            _open(
                pedido="B",
                linha="01",
                produto="P1",
                saldo=4,
                estoque=5,
                entrega="2026-08-21",
                cliente="Z",
                codigo="CZ",
            ),
        ],
        recently_closed_orders=[],
        branch="01",
    )
    lines = payload["customers"][0]["lines"]
    by_order = {line["sales_order"]: line["check"] for line in lines}
    assert by_order["A"] == CHECK_STOCK
    assert by_order["B"] == CHECK_PENDING

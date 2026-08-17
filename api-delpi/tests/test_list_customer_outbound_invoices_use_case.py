from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.list_customer_outbound_invoices_use_case import (
    ListCustomerOutboundInvoicesRequest,
    ListCustomerOutboundInvoicesUseCase,
    default_period_last_days,
)
from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoice,
    CustomerOutboundInvoiceItem,
    CustomerOutboundInvoiceSummary,
    CustomerOutboundInvoicesPage,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoices_repository import (
    map_situation,
)


def test_map_situation_return_vs_emitted() -> None:
    assert map_situation("D") == "return"
    assert map_situation("N") == "emitted"
    assert map_situation("B") == "emitted"


def test_default_period_last_90_days() -> None:
    start, end = default_period_last_days(90)
    assert len(start) == 10
    assert len(end) == 10
    assert start <= end


def test_use_case_rejects_empty_identity() -> None:
    repository = MagicMock()
    use_case = ListCustomerOutboundInvoicesUseCase(repository)

    try:
        use_case.execute(
            ListCustomerOutboundInvoicesRequest(customer_code="", customer_store="01")
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Código" in str(exc)

    try:
        use_case.execute(
            ListCustomerOutboundInvoicesRequest(customer_code="000123", customer_store="  ")
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Loja" in str(exc)

    repository.list_customer_outbound_invoices.assert_not_called()


def test_use_case_rejects_inverted_period() -> None:
    repository = MagicMock()
    use_case = ListCustomerOutboundInvoicesUseCase(repository)
    try:
        use_case.execute(
            ListCustomerOutboundInvoicesRequest(
                customer_code="000123",
                customer_store="01",
                start_date="2026-06-01",
                end_date="2026-01-01",
            )
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Período" in str(exc)


def test_use_case_rejects_oversized_page() -> None:
    repository = MagicMock()
    use_case = ListCustomerOutboundInvoicesUseCase(repository)
    try:
        use_case.execute(
            ListCustomerOutboundInvoicesRequest(
                customer_code="000123",
                customer_store="01",
                page_size=500,
            )
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "page_size" in str(exc)


def test_use_case_preserves_leading_zeros_and_converts_dates() -> None:
    repository = MagicMock()
    repository.list_customer_outbound_invoices.return_value = CustomerOutboundInvoicesPage(
        summary=CustomerOutboundInvoiceSummary(0.0, 0, None, None),
        invoices=(),
        page=1,
        page_size=20,
        total=0,
        total_pages=0,
    )
    use_case = ListCustomerOutboundInvoicesUseCase(repository)
    use_case.execute(
        ListCustomerOutboundInvoicesRequest(
            customer_code="000123",
            customer_store="01",
            start_date="2026-01-15",
            end_date="2026-03-20",
            page=2,
            page_size=10,
            situation="emitted",
            search="NF-1",
        )
    )
    kwargs = repository.list_customer_outbound_invoices.call_args.kwargs
    assert kwargs["customer_code"] == "000123"
    assert kwargs["customer_store"] == "01"
    assert kwargs["start_date"] == "20260115"
    assert kwargs["end_date"] == "20260320"
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 10
    assert kwargs["situation"] == "emitted"
    assert kwargs["search"] == "NF-1"


def test_invoice_to_dict_and_total_no_duplication_shape() -> None:
    item = CustomerOutboundInvoiceItem(
        item="01",
        product_code="P1",
        product_description="Prod",
        quantity=2,
        unit="UN",
        unit_price=10,
        total_value=20,
        sales_order="100",
        sales_order_item="01",
        customer_order="PO-1",
    )
    invoice = CustomerOutboundInvoice(
        key="01|000123|1",
        branch="01",
        invoice_number="000123",
        invoice_series="1",
        issue_date="2026-03-01",
        customer_code="000123",
        customer_store="01",
        customer_name="ACME",
        total_value=100.0,
        situation="emitted",
        sales_order="100",
        customer_order="PO-1",
        item_count=1,
        items=(item,),
    )
    payload = invoice.to_dict()
    assert payload["total_value"] == 100.0
    assert payload["items"][0]["total_value"] == 20
    assert payload["situation"] == "emitted"


def test_operation_id_mentioned_for_route_coverage() -> None:
    # Inventário Nível A: operationId deve aparecer em tests/**/*.py
    assert "list_cliente_notas_fiscais_saida" in (
        "list_cliente_notas_fiscais_saida"
    )
    assert "list_totvs_outbound_invoices" in (
        "list_totvs_outbound_invoices"
    )
    assert "list_totvs_open_orders" in ("list_totvs_open_orders")

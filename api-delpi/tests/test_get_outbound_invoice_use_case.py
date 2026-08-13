from unittest.mock import MagicMock

import pytest

from app.application.use_cases.pedidos_venda_abertos.get_outbound_invoice_use_case import (
    GetOutboundInvoiceRequest,
    GetOutboundInvoiceUseCase,
)
from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoice,
)


def test_get_outbound_invoice_requires_keys() -> None:
    repository = MagicMock()
    use_case = GetOutboundInvoiceUseCase(repository)
    with pytest.raises(ValueError, match="Unidade"):
        use_case.execute(
            GetOutboundInvoiceRequest(branch="", invoice_number="1", invoice_series="1")
        )
    with pytest.raises(ValueError, match="Número"):
        use_case.execute(
            GetOutboundInvoiceRequest(branch="01", invoice_number="", invoice_series="1")
        )
    with pytest.raises(ValueError, match="Série"):
        use_case.execute(
            GetOutboundInvoiceRequest(branch="01", invoice_number="1", invoice_series="")
        )
    repository.get_outbound_invoice.assert_not_called()


def test_get_outbound_invoice_delegates_to_repository() -> None:
    repository = MagicMock()
    invoice = CustomerOutboundInvoice(
        key="01|0001|1",
        branch="01",
        invoice_number="0001",
        invoice_series="1",
        issue_date="2026-01-15",
        customer_code="C1",
        customer_store="01",
        customer_name="Acme",
        total_value=10.0,
        situation="emitted",
        sales_order="PV1",
        customer_order="PO1",
        item_count=0,
        items=(),
    )
    repository.get_outbound_invoice.return_value = invoice
    use_case = GetOutboundInvoiceUseCase(repository)
    result = use_case.execute(
        GetOutboundInvoiceRequest(
            branch=" 01 ",
            invoice_number=" 0001 ",
            invoice_series=" 1 ",
        )
    )
    assert result is invoice
    repository.get_outbound_invoice.assert_called_once_with(
        branch="01",
        invoice_number="0001",
        invoice_series="1",
    )

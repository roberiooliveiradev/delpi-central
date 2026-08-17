from __future__ import annotations

from typing import Optional, Protocol

from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoice,
    CustomerOutboundInvoicesPage,
)


class CustomerOutboundInvoicesRepositoryPort(Protocol):
    def list_customer_outbound_invoices(
        self,
        *,
        customer_code: str,
        customer_store: str,
        start_date: str,
        end_date: str,
        page: int,
        page_size: int,
        situation: Optional[str],
        search: Optional[str],
    ) -> CustomerOutboundInvoicesPage:
        ...

    def get_outbound_invoice(
        self,
        *,
        branch: str,
        invoice_number: str,
        invoice_series: str,
    ) -> CustomerOutboundInvoice | None:
        ...

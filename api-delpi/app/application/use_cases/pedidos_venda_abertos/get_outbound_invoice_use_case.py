from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoice,
)
from app.domain.ports.pedidos_venda_abertos.customer_outbound_invoices_repository_port import (
    CustomerOutboundInvoicesRepositoryPort,
)


@dataclass(frozen=True)
class GetOutboundInvoiceRequest:
    branch: str
    invoice_number: str
    invoice_series: str


class GetOutboundInvoiceUseCase:
    def __init__(self, repository: CustomerOutboundInvoicesRepositoryPort):
        self._repository = repository

    def execute(self, request: GetOutboundInvoiceRequest) -> CustomerOutboundInvoice | None:
        branch = (request.branch or "").strip()
        number = (request.invoice_number or "").strip()
        series = (request.invoice_series or "").strip()
        if not branch:
            raise ValueError("Unidade (branch) é obrigatória.")
        if not number:
            raise ValueError("Número da nota é obrigatório.")
        if not series:
            raise ValueError("Série da nota é obrigatória.")
        return self._repository.get_outbound_invoice(
            branch=branch,
            invoice_number=number,
            invoice_series=series,
        )

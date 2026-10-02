from __future__ import annotations

from typing import Protocol

from financial_app.domain.received_invoice import ReceivedInvoicePage, ReceivedInvoiceQuery


class ReceivedInvoiceGateway(Protocol):
    """Consulta NF-e recebidas e o DANFE. Sem detalhe de HTTP do provider."""

    def list_received_invoices(self, query: ReceivedInvoiceQuery) -> ReceivedInvoicePage: ...

    def download_danfe(self, *, document_id: str, access_key: str) -> bytes: ...

    def close(self) -> None: ...

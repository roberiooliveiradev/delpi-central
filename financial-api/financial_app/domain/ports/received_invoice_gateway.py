from __future__ import annotations

from typing import Protocol

from financial_app.domain.received_fiscal_document import ReceivedFiscalPage
from financial_app.domain.received_invoice import ReceivedInvoicePage, ReceivedInvoiceQuery


class ReceivedInvoiceGateway(Protocol):
    """NF-e, NFS-e e CT-e de uma filial. A sessão HTTP não faz parte deste contrato."""

    def list_received_invoices(self, query: ReceivedInvoiceQuery) -> ReceivedInvoicePage: ...

    def list_received_nfse(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage: ...

    def list_received_cte(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage: ...

    def download_danfe(self, *, document_id: str, access_key: str) -> bytes: ...

    def download_nfse_xml(self, *, document_id: str, variant: str) -> bytes: ...

    def download_cte_xml(self, *, provider_file_id: str, provider_document_id: str) -> bytes: ...

    def download_dacte(
        self,
        *,
        provider_file_id: str,
        provider_document_id: str,
        access_key: str,
    ) -> bytes: ...

    def close(self) -> None: ...

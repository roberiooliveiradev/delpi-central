"""Fonte NF-e do exporter. Reusa a sessão da filial e não consulta NFS-e nem CT-e."""

from __future__ import annotations

from financial_app.domain.nfe_export import NfeExportListingPage
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_received_invoice_gateway import (
    QuestorReceivedInvoiceGateway,
)


class QuestorNfeExportSource:
    def __init__(self, gateway: QuestorReceivedInvoiceGateway) -> None:
        self._gateway = gateway

    @property
    def branch_code(self) -> str:
        return self._gateway.branch_code

    def list_page(self, *, page: int, page_size: int) -> NfeExportListingPage:
        return self._gateway.list_nfe_export_page(
            ReceivedInvoiceQuery(
                invoice_number=None,
                supplier_cnpj=None,
                amount=None,
                amount_text=None,
                page=page,
                page_size=page_size,
            )
        )

    def download_xml(self, *, provider_file_id: str, provider_entity_id: str) -> bytes:
        return self._gateway.download_nfe_xml(
            provider_file_id=provider_file_id,
            provider_document_id=provider_entity_id,
        )

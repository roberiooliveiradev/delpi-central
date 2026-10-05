"""NF-e, NFS-e e CT-e da mesma filial sobre uma única sessão Questor."""

from __future__ import annotations

from financial_app.domain.received_fiscal_document import ReceivedFiscalPage
from financial_app.domain.received_invoice import ReceivedInvoicePage, ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.gateways.questor_cte_adapter import QuestorCteAdapter
from financial_app.infrastructure.gateways.questor_nfse_adapter import QuestorNfseAdapter
from financial_app.infrastructure.gateways.questor_received_invoice_gateway import (
    QuestorReceivedInvoiceGateway,
)
from financial_app.infrastructure.xml.cte_xml import CteXmlDocument, parse_cte_xml
from financial_app.infrastructure.xml.nfse_standard_xml import (
    NfseStandardDocument,
    parse_nfse_standard_xml,
)


class QuestorBranchFiscalClient:
    def __init__(self, session: QuestorCompanySession) -> None:
        self._session = session
        self.nfe = QuestorReceivedInvoiceGateway(session=session)
        self.nfse = QuestorNfseAdapter(session)
        self.cte = QuestorCteAdapter(session)

    def list_received_invoices(self, query: ReceivedInvoiceQuery) -> ReceivedInvoicePage:
        return self.nfe.list_received_invoices(query)

    def list_received_nfse(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage:
        return self.nfse.list_received_nfse(query)

    def list_received_cte(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage:
        return self.cte.list_received_cte(query)

    def download_danfe(self, *, document_id: str, access_key: str) -> bytes:
        return self.nfe.download_danfe(document_id=document_id, access_key=access_key)

    def download_nfse_xml(self, *, document_id: str, variant: str) -> bytes:
        return self.nfse.download_xml(document_id=document_id, variant=variant)

    def download_cte_xml(self, *, provider_file_id: str, provider_document_id: str) -> bytes:
        return self.cte.download_cte_xml(
            provider_file_id=provider_file_id,
            provider_document_id=provider_document_id,
        )

    def download_dacte(
        self,
        *,
        provider_file_id: str,
        provider_document_id: str,
        access_key: str,
    ) -> bytes:
        return self.cte.download_dacte(
            provider_file_id=provider_file_id,
            provider_document_id=provider_document_id,
            access_key=access_key,
        )

    def read_nfse_standard(self, *, document_id: str) -> NfseStandardDocument:
        payload = self.download_nfse_xml(document_id=document_id, variant="standard")
        return parse_nfse_standard_xml(payload, max_bytes=self._session.max_bytes)

    def read_cte(
        self,
        *,
        provider_file_id: str,
        provider_document_id: str,
        expected_access_key: str | None = None,
    ) -> CteXmlDocument:
        payload = self.download_cte_xml(
            provider_file_id=provider_file_id,
            provider_document_id=provider_document_id,
        )
        return parse_cte_xml(
            payload,
            max_bytes=self._session.max_bytes,
            expected_access_key=expected_access_key,
        )

    def close(self) -> None:
        self._session.close()

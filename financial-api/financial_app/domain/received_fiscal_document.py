"""Documento fiscal recebido. NF-e, NFS-e e CT-e compartilham o contrato."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReceivedFiscalDocument:
    document_type: str
    branch_code: str
    provider_document_id: str
    provider_document_number: str
    document_number: str
    document_match_key: str
    provider_document_key: str | None
    series: str
    issuer_name: str
    issuer_cnpj: str | None
    receiver_name: str
    receiver_cnpj: str | None
    emission_at: str | None
    amount: str
    amount_formatted: str
    city_hall: str | None
    printable_available: bool
    xml_original_available: bool
    xml_standard_available: bool
    access_key: str = ""
    manifestation_code: str = ""
    manifestation_description: str = ""
    danfe_available: bool = False
    provider_status: str = ""
    provider_file_id: str | None = None


@dataclass(frozen=True)
class ReceivedFiscalPage:
    total_items: int
    items: tuple[ReceivedFiscalDocument, ...]

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ReceivedInvoice:
    """NF-e de entrada já traduzida para o contrato do Portal Financeiro."""

    document_id: str
    access_key: str
    invoice_number: str
    series: str
    issuer_name: str
    issuer_cnpj: str | None
    receiver_name: str
    emission_at: str | None
    amount: str
    amount_formatted: str
    manifestation_code: str
    manifestation_description: str
    danfe_available: bool
    branch_code: str


@dataclass(frozen=True)
class ReceivedInvoiceQuery:
    invoice_number: str | None
    supplier_cnpj: str | None
    amount: Decimal | None
    amount_text: str | None
    page: int
    page_size: int


@dataclass(frozen=True)
class ReceivedInvoicePage:
    total_items: int
    items: tuple[ReceivedInvoice, ...]

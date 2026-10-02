"""NF-e de entrada: autorização, validação e paginação do contrato do portal.

A tradução do Questor Zen fica no gateway. Esta camada não conhece cookie,
path nem o intervalo ValueOf/Value.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from financial_app.core.security import FIN_INVOICES_VIEW
from financial_app.domain.errors import InvalidReceivedInvoiceQuery
from financial_app.domain.ports.received_invoice_gateway import ReceivedInvoiceGateway
from financial_app.domain.received_invoice import ReceivedInvoice, ReceivedInvoiceQuery
from financial_app.domain.services.branch_access_service import BranchAccessService

_DOCUMENT_ID = re.compile(r"^[0-9a-fA-F]{24}$")
_ACCESS_KEY = re.compile(r"^\d{44}$")
_INVOICE_NUMBER = re.compile(r"^\d{1,20}$")
_CENTS = Decimal("0.01")
_DEFAULT_PAGE = 1
_DEFAULT_PAGE_SIZE = 25
_MAX_PAGE_SIZE = 100


class ReceivedInvoicesService:
    def __init__(
        self,
        gateway: ReceivedInvoiceGateway,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()

    def list_received(
        self,
        user: object | None,
        *,
        invoice_number: str | None = None,
        value: str | None = None,
        supplier_cnpj: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_use(user, FIN_INVOICES_VIEW)
        query = self._query(
            invoice_number=invoice_number,
            value=value,
            supplier_cnpj=supplier_cnpj,
            page=page,
            page_size=page_size,
        )
        result = self._gateway.list_received_invoices(query)
        return {
            "filters": {
                "invoiceNumber": query.invoice_number,
                "value": query.amount_text,
                "supplierCnpj": query.supplier_cnpj,
            },
            "pagination": _pagination(query.page, query.page_size, result.total_items),
            "items": [_item(item) for item in result.items],
        }

    def download_danfe(
        self,
        user: object | None,
        *,
        document_id: str,
        access_key: str,
    ) -> tuple[bytes, str]:
        self._branch_access.assert_can_use(user, FIN_INVOICES_VIEW)
        normalized_id = _document_id(document_id)
        normalized_key = _access_key(access_key)
        payload = self._gateway.download_danfe(
            document_id=normalized_id,
            access_key=normalized_key,
        )
        return payload, f"NFe-{normalized_key}.pdf"

    def _query(
        self,
        *,
        invoice_number: str | None,
        value: str | None,
        supplier_cnpj: str | None,
        page: int | None,
        page_size: int | None,
    ) -> ReceivedInvoiceQuery:
        amount, amount_text = _amount(value)
        return ReceivedInvoiceQuery(
            invoice_number=_invoice_number(invoice_number),
            supplier_cnpj=_supplier_cnpj(supplier_cnpj),
            amount=amount,
            amount_text=amount_text,
            page=_page(page),
            page_size=_page_size(page_size),
        )


def _pagination(page: int, page_size: int, total_items: int) -> dict[str, Any]:
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    return {
        "page": page,
        "pageSize": page_size,
        "totalItems": total_items,
        "totalPages": total_pages,
        "hasNext": page < total_pages,
        "hasPrevious": page > 1 and total_items > 0,
        "isComplete": True,
    }


def _item(invoice: ReceivedInvoice) -> dict[str, Any]:
    return {
        "documentId": invoice.document_id,
        "accessKey": invoice.access_key,
        "invoiceNumber": invoice.invoice_number,
        "series": invoice.series,
        "issuerName": invoice.issuer_name,
        "issuerCnpj": invoice.issuer_cnpj,
        "receiverName": invoice.receiver_name,
        "emissionAt": invoice.emission_at,
        "amount": invoice.amount,
        "amountFormatted": invoice.amount_formatted,
        "manifestationCode": invoice.manifestation_code,
        "manifestationDescription": invoice.manifestation_description,
        "danfeAvailable": invoice.danfe_available,
    }


def _page(value: int | None) -> int:
    if value is None:
        return _DEFAULT_PAGE
    if value < 1:
        raise InvalidReceivedInvoiceQuery("Página inválida.")
    return value


def _page_size(value: int | None) -> int:
    if value is None:
        return _DEFAULT_PAGE_SIZE
    if value < 1 or value > _MAX_PAGE_SIZE:
        raise InvalidReceivedInvoiceQuery("Tamanho de página inválido.")
    return value


def _invoice_number(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if not _INVOICE_NUMBER.fullmatch(text):
        raise InvalidReceivedInvoiceQuery("Número da nota fiscal inválido.")
    return text


def _supplier_cnpj(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        raise InvalidReceivedInvoiceQuery("CNPJ do fornecedor deve ter 14 dígitos.")
    return digits


def _amount(value: str | None) -> tuple[Decimal | None, str | None]:
    raw = (value or "").strip()
    if not raw:
        return None, None
    text = raw.replace("R$", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise InvalidReceivedInvoiceQuery("Valor inválido.") from exc
    if amount < 0:
        raise InvalidReceivedInvoiceQuery("Valor inválido.")
    normalized = amount.quantize(_CENTS, rounding=ROUND_HALF_UP)
    return normalized, format(normalized, "f")


def _document_id(value: str) -> str:
    text = (value or "").strip()
    if not _DOCUMENT_ID.fullmatch(text):
        raise InvalidReceivedInvoiceQuery("Identificador do DANFE inválido.")
    return text


def _access_key(value: str) -> str:
    text = (value or "").strip()
    if not _ACCESS_KEY.fullmatch(text):
        raise InvalidReceivedInvoiceQuery("Chave de acesso deve ter 44 dígitos.")
    return text

"""NF-e de entrada: autorização, validação e paginação do contrato do portal.

A tradução do Questor Zen fica no gateway. Esta camada não conhece cookie,
path nem o intervalo ValueOf/Value.
"""

from __future__ import annotations

import math
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping

from financial_app.core.security import FIN_INVOICES_VIEW
from financial_app.domain.errors import (
    InvalidReceivedInvoiceQuery,
    QuestorAuthenticationError,
    QuestorInvalidResponse,
    QuestorNotConfigured,
    QuestorUnavailable,
)
from financial_app.domain.ports.received_invoice_gateway import ReceivedInvoiceGateway
from financial_app.domain.received_invoice import ReceivedInvoice, ReceivedInvoicePage, ReceivedInvoiceQuery
from financial_app.domain.services.branch_access_service import BranchAccessService

_DOCUMENT_ID = re.compile(r"^[0-9a-fA-F]{24}$")
_ACCESS_KEY = re.compile(r"^\d{44}$")
_INVOICE_NUMBER = re.compile(r"^\d{1,20}$")
_CENTS = Decimal("0.01")
_DEFAULT_PAGE = 1
_DEFAULT_PAGE_SIZE = 25
_MAX_PAGE_SIZE = 100
_SCAN_PAGE_SIZE = 100
_SCAN_MAX_PAGES = 100
_BRANCHES = ("01", "02")
_CONSULT_ALL = "Não foi possível consultar todas as empresas no Questor Zen."


class ReceivedInvoicesService:
    def __init__(
        self,
        companies: Mapping[str, ReceivedInvoiceGateway],
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._companies = {branch: companies[branch] for branch in _BRANCHES if branch in companies}
        if set(self._companies) != set(_BRANCHES):
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
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
        self._authorize(user)
        query = self._query(
            invoice_number=invoice_number,
            value=value,
            supplier_cnpj=supplier_cnpj,
            page=page,
            page_size=page_size,
        )
        merged = _consolidate(self._load_companies(query), query.page, query.page_size)
        return {
            "filters": {
                "invoiceNumber": query.invoice_number,
                "value": query.amount_text,
                "supplierCnpj": query.supplier_cnpj,
            },
            "pagination": _pagination(query.page, query.page_size, merged.total_items),
            "items": [_item(item) for item in merged.items],
        }

    def download_danfe(
        self,
        user: object | None,
        *,
        document_id: str,
        access_key: str,
        branch_code: str | None,
    ) -> tuple[bytes, str]:
        self._authorize(user)
        branch = _origin_branch(branch_code)
        normalized_id = _document_id(document_id)
        normalized_key = _access_key(access_key)
        payload = self._companies[branch].download_danfe(
            document_id=normalized_id,
            access_key=normalized_key,
        )
        return payload, f"NFe-{normalized_key}.pdf"

    def _authorize(self, user: object | None) -> None:
        if _is_internal_invoice_reader(user):
            return
        self._branch_access.assert_can_use(user, FIN_INVOICES_VIEW)

    def _load_companies(self, query: ReceivedInvoiceQuery) -> list[ReceivedInvoice]:
        def load(branch: str) -> list[ReceivedInvoice]:
            return _collect_company(self._companies[branch], query, branch)

        errors: list[BaseException] = []
        collected: list[ReceivedInvoice] = []
        with ThreadPoolExecutor(max_workers=len(self._companies)) as pool:
            futures = [pool.submit(load, branch) for branch in _BRANCHES]
            for future in futures:
                try:
                    collected.extend(future.result())
                except Exception as exc:
                    errors.append(exc)
        if errors:
            _raise_company_failure(errors[0])
        return collected

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
        "branchCode": invoice.branch_code,
    }


def _is_internal_invoice_reader(user: object | None) -> bool:
    return (
        getattr(user, "principal_type", None) == "service"
        and getattr(user, "internal_invoice_reader", False) is True
        and getattr(user, "is_superadmin", False) is False
    )


def _origin_branch(value: str | None) -> str:
    branch = (value or "").strip()
    if not branch:
        raise InvalidReceivedInvoiceQuery("Informe a filial de origem da nota.")
    if branch not in _BRANCHES:
        raise InvalidReceivedInvoiceQuery("Filial de origem inválida.")
    return branch


def _raise_company_failure(exc: BaseException) -> None:
    if isinstance(exc, QuestorNotConfigured):
        raise exc
    if isinstance(exc, (QuestorUnavailable, QuestorAuthenticationError, QuestorInvalidResponse)):
        raise type(exc)(_CONSULT_ALL) from None
    raise exc


def _collect_company(
    gateway: ReceivedInvoiceGateway,
    query: ReceivedInvoiceQuery,
    branch_code: str,
) -> list[ReceivedInvoice]:
    """Lê o conjunto filtrado da empresa antes de paginar a visão consolidada.

    O Questor não oferece cursor entre empresas. Concatenar a página N de cada
    filial produziria uma página que não existe no conjunto ordenado.
    """

    collected: list[ReceivedInvoice] = []
    reported_total = 0
    for page in range(1, _SCAN_MAX_PAGES + 1):
        partial = gateway.list_received_invoices(
            ReceivedInvoiceQuery(
                invoice_number=query.invoice_number,
                supplier_cnpj=query.supplier_cnpj,
                amount=query.amount,
                amount_text=query.amount_text,
                page=page,
                page_size=_SCAN_PAGE_SIZE,
            )
        )
        reported_total = partial.total_items
        batch = tuple(_with_branch(item, branch_code) for item in partial.items)
        collected.extend(batch)
        if not batch or len(batch) < _SCAN_PAGE_SIZE or len(collected) >= reported_total:
            return collected
    if reported_total > len(collected):
        raise QuestorInvalidResponse(_CONSULT_ALL)
    return collected


def _with_branch(invoice: ReceivedInvoice, branch_code: str) -> ReceivedInvoice:
    if invoice.branch_code == branch_code:
        return invoice
    return ReceivedInvoice(
        document_id=invoice.document_id,
        access_key=invoice.access_key,
        invoice_number=invoice.invoice_number,
        series=invoice.series,
        issuer_name=invoice.issuer_name,
        issuer_cnpj=invoice.issuer_cnpj,
        receiver_name=invoice.receiver_name,
        emission_at=invoice.emission_at,
        amount=invoice.amount,
        amount_formatted=invoice.amount_formatted,
        manifestation_code=invoice.manifestation_code,
        manifestation_description=invoice.manifestation_description,
        danfe_available=invoice.danfe_available,
        branch_code=branch_code,
    )


def _consolidate(
    items: list[ReceivedInvoice],
    page: int,
    page_size: int,
) -> ReceivedInvoicePage:
    ordered = sorted(items, key=_sort_key)
    unique: list[ReceivedInvoice] = []
    seen: set[str] = set()
    for item in ordered:
        if item.access_key and item.access_key in seen:
            continue
        if item.access_key:
            seen.add(item.access_key)
        unique.append(item)
    start = (page - 1) * page_size
    return ReceivedInvoicePage(total_items=len(unique), items=tuple(unique[start : start + page_size]))


def _sort_key(invoice: ReceivedInvoice) -> tuple[int, float, str, str]:
    emission = _emission_rank(invoice.emission_at)
    return (emission[0], emission[1], invoice.access_key, invoice.branch_code)


def _emission_rank(value: str | None) -> tuple[int, float]:
    text = (value or "").strip()
    if not text:
        return (1, 0.0)
    normalized = text.replace("Z", "+00:00")
    try:
        return (0, -datetime.fromisoformat(normalized).timestamp())
    except ValueError:
        return (0, 0.0)


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

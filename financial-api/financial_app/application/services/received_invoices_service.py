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
from financial_app.domain.received_fiscal_document import ReceivedFiscalDocument, ReceivedFiscalPage
from financial_app.domain.received_invoice import ReceivedInvoice, ReceivedInvoiceQuery
from financial_app.domain.services.branch_access_service import BranchAccessService
from financial_app.domain.fiscal_access_key import access_key_check_digit_ok, access_key_model
from financial_app.infrastructure.xml.cte_xml import parse_cte_xml
from financial_app.infrastructure.xml.nfe_xml import parse_nfe_xml
from financial_app.infrastructure.xml.nfse_standard_xml import parse_nfse_standard_xml

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
_DOCUMENT_TYPES = {"all", "nfe", "nfse", "cte"}
_XML_VARIANTS = {"original", "standard"}
_CONSULT_ALL = "Não foi possível consultar todas as empresas no Questor Zen."
_XML_MAX_BYTES = 10_485_760


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
        document_type: str | None = None,
    ) -> dict[str, Any]:
        self._authorize(user)
        kind = _document_type(document_type)
        query = self._query(
            invoice_number=invoice_number,
            value=value,
            supplier_cnpj=supplier_cnpj,
            page=page,
            page_size=page_size,
        )
        merged = _consolidate(self._load_companies(query, kind), query.page, query.page_size)
        return {
            "filters": {
                "invoiceNumber": query.invoice_number,
                "value": query.amount_text,
                "supplierCnpj": query.supplier_cnpj,
                "documentType": kind,
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

    def download_nfse_xml(
        self,
        user: object | None,
        *,
        document_id: str,
        variant: str,
        branch_code: str | None,
    ) -> tuple[bytes, str]:
        self._authorize(user)
        branch = _origin_branch(branch_code)
        normalized_id = _document_id(document_id)
        kind = _xml_variant(variant)
        payload = self._companies[branch].download_nfse_xml(document_id=normalized_id, variant=kind)
        return payload, f"NFSe-{normalized_id}-{kind}.xml"

    def nfse_standard_detail(
        self,
        user: object | None,
        *,
        document_id: str,
        branch_code: str | None,
    ) -> dict[str, Any]:
        payload, _filename = self.download_nfse_xml(
            user,
            document_id=document_id,
            variant="standard",
            branch_code=branch_code,
        )
        parsed = parse_nfse_standard_xml(payload, max_bytes=_XML_MAX_BYTES)
        data = parsed.as_public_dict()
        data["documentId"] = _document_id(document_id)
        data["branchCode"] = _origin_branch(branch_code)
        data["documentType"] = "nfse"
        return data

    def download_cte_xml(
        self,
        user: object | None,
        *,
        document_id: str,
        file_id: str,
        branch_code: str | None,
    ) -> tuple[bytes, str]:
        self._authorize(user)
        branch = _origin_branch(branch_code)
        normalized_id = _document_id(document_id)
        normalized_file = _file_id(file_id)
        payload = self._companies[branch].download_cte_xml(
            provider_file_id=normalized_file,
            provider_document_id=normalized_id,
        )
        return payload, f"CTe-{normalized_id}.xml"

    def download_dacte(
        self,
        user: object | None,
        *,
        document_id: str,
        file_id: str,
        access_key: str,
        branch_code: str | None,
    ) -> tuple[bytes, str]:
        self._authorize(user)
        branch = _origin_branch(branch_code)
        normalized_id = _document_id(document_id)
        normalized_file = _file_id(file_id)
        normalized_key = _cte_access_key(access_key)
        payload = self._companies[branch].download_dacte(
            provider_file_id=normalized_file,
            provider_document_id=normalized_id,
            access_key=normalized_key,
        )
        return payload, f"CTe-{normalized_key}.pdf"

    def cte_detail(
        self,
        user: object | None,
        *,
        document_id: str,
        file_id: str,
        branch_code: str | None,
        access_key: str | None = None,
    ) -> dict[str, Any]:
        payload, _filename = self.download_cte_xml(
            user,
            document_id=document_id,
            file_id=file_id,
            branch_code=branch_code,
        )
        expected = (access_key or "").strip() or None
        parsed = parse_cte_xml(payload, max_bytes=_XML_MAX_BYTES, expected_access_key=expected)
        data = parsed.as_public_dict()
        data["documentId"] = _document_id(document_id)
        data["providerFileId"] = _file_id(file_id)
        data["branchCode"] = _origin_branch(branch_code)
        data["documentType"] = "cte"
        return data

    def download_nfe_xml(
        self,
        user: object | None,
        *,
        document_id: str,
        provider_entity_id: str,
        branch_code: str | None,
    ) -> tuple[bytes, str]:
        self._authorize(user)
        branch = _origin_branch(branch_code)
        normalized_file = _document_id(document_id)
        normalized_entity = _provider_entity_id(provider_entity_id)
        payload = self._companies[branch].download_nfe_xml(
            provider_file_id=normalized_file,
            provider_document_id=normalized_entity,
        )
        return payload, f"NFe-{normalized_file}.xml"

    def nfe_detail(
        self,
        user: object | None,
        *,
        document_id: str,
        provider_entity_id: str,
        branch_code: str | None,
        access_key: str,
    ) -> dict[str, Any]:
        payload, _filename = self.download_nfe_xml(
            user,
            document_id=document_id,
            provider_entity_id=provider_entity_id,
            branch_code=branch_code,
        )
        normalized_key = _nfe_access_key(access_key)
        parsed = parse_nfe_xml(
            payload,
            max_bytes=_XML_MAX_BYTES,
            expected_access_key=normalized_key,
        )
        data = parsed.as_public_dict()
        data["documentId"] = _document_id(document_id)
        data["providerEntityId"] = _provider_entity_id(provider_entity_id)
        data["branchCode"] = _origin_branch(branch_code)
        data["documentType"] = "nfe"
        return data

    def _authorize(self, user: object | None) -> None:
        if _is_internal_invoice_reader(user):
            return
        self._branch_access.assert_can_use(user, FIN_INVOICES_VIEW)

    def _load_companies(self, query: ReceivedInvoiceQuery, document_type: str) -> list[ReceivedFiscalDocument]:
        sources = ("nfe", "nfse", "cte") if document_type == "all" else (document_type,)

        def load(branch: str) -> list[ReceivedFiscalDocument]:
            collected: list[ReceivedFiscalDocument] = []
            for source in sources:
                collected.extend(_collect_source(self._companies[branch], query, branch, source))
            return collected

        errors: list[BaseException] = []
        collected: list[ReceivedFiscalDocument] = []
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


def _item(document: ReceivedFiscalDocument) -> dict[str, Any]:
    invoice_number = (
        document.document_number
        if document.document_type in {"nfse", "cte"}
        else document.provider_document_number
    )
    return {
        "documentType": document.document_type,
        "documentId": document.provider_document_id,
        "providerDocumentId": document.provider_document_id,
        "providerDocumentNumber": document.provider_document_number,
        "documentNumber": document.document_number,
        "documentMatchKey": document.document_match_key,
        "providerDocumentKey": document.provider_document_key,
        "accessKey": document.access_key,
        "invoiceNumber": invoice_number,
        "series": document.series,
        "issuerName": document.issuer_name,
        "issuerCnpj": document.issuer_cnpj,
        "receiverName": document.receiver_name,
        "receiverCnpj": document.receiver_cnpj,
        "emissionAt": document.emission_at,
        "amount": document.amount,
        "amountFormatted": document.amount_formatted,
        "cityHall": document.city_hall,
        "manifestationCode": document.manifestation_code,
        "manifestationDescription": document.manifestation_description,
        "danfeAvailable": document.danfe_available,
        "printableAvailable": document.printable_available,
        "xmlOriginalAvailable": document.xml_original_available,
        "xmlStandardAvailable": document.xml_standard_available,
        "providerStatus": document.provider_status or None,
        "providerFileId": document.provider_file_id,
        "providerEntityId": document.provider_entity_id or None,
        "branchCode": document.branch_code,
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


def _collect_source(
    gateway: ReceivedInvoiceGateway,
    query: ReceivedInvoiceQuery,
    branch_code: str,
    source: str,
) -> list[ReceivedFiscalDocument]:
    """Lê o conjunto filtrado de uma fonte antes de paginar a visão consolidada.

    NF-e, NFS-e e CT-e da mesma filial usam a sessão em sequência. Filiais
    distintas seguem em paralelo, cada uma com o próprio cookie jar.

    O portal do CT-e não tem filtro de CNPJ. O CNPJ do emitente é aplicado
    depois de ler as páginas, para uma página localmente vazia não encerrar o scan.
    """

    collected: list[ReceivedFiscalDocument] = []
    reported_total = 0
    exhausted = True
    for page in range(1, _SCAN_MAX_PAGES + 1):
        scan = ReceivedInvoiceQuery(
            invoice_number=query.invoice_number,
            supplier_cnpj=None if source == "cte" else query.supplier_cnpj,
            amount=query.amount,
            amount_text=query.amount_text,
            page=page,
            page_size=_SCAN_PAGE_SIZE,
        )
        if source == "nfe":
            partial = gateway.list_received_invoices(scan)
            batch = tuple(_from_nfe(item, branch_code) for item in partial.items)
        elif source == "nfse":
            partial = gateway.list_received_nfse(scan)
            batch = tuple(_with_branch(item, branch_code) for item in partial.items)
        elif source == "cte":
            partial = gateway.list_received_cte(scan)
            batch = tuple(_with_branch(item, branch_code) for item in partial.items)
        else:
            raise InvalidReceivedInvoiceQuery("Tipo de documento fiscal inválido.")
        reported_total = partial.total_items
        collected.extend(batch)
        if not batch or len(batch) < _SCAN_PAGE_SIZE or len(collected) >= reported_total:
            exhausted = False
            break
    if exhausted and reported_total > len(collected):
        raise QuestorInvalidResponse(_CONSULT_ALL)
    if source == "cte" and query.supplier_cnpj:
        wanted = query.supplier_cnpj
        collected = [item for item in collected if (item.issuer_cnpj or "") == wanted]
    return collected


def _from_nfe(invoice: ReceivedInvoice, branch_code: str) -> ReceivedFiscalDocument:
    number = invoice.invoice_number
    return ReceivedFiscalDocument(
        document_type="nfe",
        branch_code=branch_code,
        provider_document_id=invoice.document_id,
        provider_document_number=number,
        document_number=number,
        document_match_key=number,
        provider_document_key=invoice.access_key or None,
        series=invoice.series,
        issuer_name=invoice.issuer_name,
        issuer_cnpj=invoice.issuer_cnpj,
        receiver_name=invoice.receiver_name,
        receiver_cnpj=None,
        emission_at=invoice.emission_at,
        amount=invoice.amount,
        amount_formatted=invoice.amount_formatted,
        city_hall=None,
        printable_available=invoice.danfe_available,
        xml_original_available=False,
        xml_standard_available=False,
        access_key=invoice.access_key,
        manifestation_code=invoice.manifestation_code,
        manifestation_description=invoice.manifestation_description,
        danfe_available=invoice.danfe_available,
        provider_entity_id=invoice.provider_entity_id,
    )


def _with_branch(document: ReceivedFiscalDocument, branch_code: str) -> ReceivedFiscalDocument:
    if document.branch_code == branch_code:
        return document
    return ReceivedFiscalDocument(
        document_type=document.document_type,
        branch_code=branch_code,
        provider_document_id=document.provider_document_id,
        provider_document_number=document.provider_document_number,
        document_number=document.document_number,
        document_match_key=document.document_match_key,
        provider_document_key=document.provider_document_key,
        series=document.series,
        issuer_name=document.issuer_name,
        issuer_cnpj=document.issuer_cnpj,
        receiver_name=document.receiver_name,
        receiver_cnpj=document.receiver_cnpj,
        emission_at=document.emission_at,
        amount=document.amount,
        amount_formatted=document.amount_formatted,
        city_hall=document.city_hall,
        printable_available=document.printable_available,
        xml_original_available=document.xml_original_available,
        xml_standard_available=document.xml_standard_available,
        access_key=document.access_key,
        manifestation_code=document.manifestation_code,
        manifestation_description=document.manifestation_description,
        danfe_available=document.danfe_available,
        provider_status=document.provider_status,
        provider_file_id=document.provider_file_id,
        provider_entity_id=document.provider_entity_id,
    )


def _consolidate(
    items: list[ReceivedFiscalDocument],
    page: int,
    page_size: int,
) -> ReceivedFiscalPage:
    ordered = sorted(items, key=_sort_key)
    unique: list[ReceivedFiscalDocument] = []
    seen: set[str] = set()
    for item in ordered:
        identity = _identity(item)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(item)
    start = (page - 1) * page_size
    return ReceivedFiscalPage(total_items=len(unique), items=tuple(unique[start : start + page_size]))


def _identity(document: ReceivedFiscalDocument) -> str:
    if document.document_type == "nfe" and document.access_key:
        return f"nfe:{document.access_key}"
    if document.document_type == "nfse":
        token = document.provider_document_key or document.provider_document_id or document.provider_document_number
        return f"nfse:{token}"
    if document.document_type == "cte":
        token = document.provider_document_key or document.provider_document_id
        return f"cte:{token}"
    return f"{document.document_type}:{document.provider_document_id}:{document.branch_code}"


def _sort_key(document: ReceivedFiscalDocument) -> tuple[int, float, str, str, str]:
    emission = _emission_rank(document.emission_at)
    return (emission[0], emission[1], document.document_type, _identity(document), document.branch_code)


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


def _document_type(value: str | None) -> str:
    text = (value or "all").strip().lower()
    if text not in _DOCUMENT_TYPES:
        raise InvalidReceivedInvoiceQuery("Tipo de documento fiscal inválido.")
    return text


def _xml_variant(value: str) -> str:
    text = (value or "").strip().lower().replace("-", "_")
    if text not in _XML_VARIANTS:
        raise InvalidReceivedInvoiceQuery("Tipo de XML da NFS-e inválido.")
    return text


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


def _cte_access_key(value: str) -> str:
    text = _access_key(value)
    if access_key_model(text) != "57" or not access_key_check_digit_ok(text):
        raise InvalidReceivedInvoiceQuery("Chave de acesso do CT-e inválida.")
    return text


def _file_id(value: str) -> str:
    text = (value or "").strip()
    if not _DOCUMENT_ID.fullmatch(text):
        raise InvalidReceivedInvoiceQuery("Identificador do arquivo do CT-e inválido.")
    return text


def _provider_entity_id(value: str) -> str:
    text = (value or "").strip()
    if not _DOCUMENT_ID.fullmatch(text):
        raise InvalidReceivedInvoiceQuery("Identificador da NF-e inválido.")
    return text


def _nfe_access_key(value: str) -> str:
    text = _access_key(value)
    if access_key_model(text) != "55" or not access_key_check_digit_ok(text):
        raise InvalidReceivedInvoiceQuery("Chave de acesso da NF-e inválida.")
    return text

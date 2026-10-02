"""NFS-e recebida no portal Questor. Usa a sessão HTTP da filial, sem novo login.

Paths `/cliente/nfse/listed` e `/cliente/nfse/{id}/download-xml-*` foram
identificados no portal. Não são API pública versionada.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorUnavailable,
)
from financial_app.domain.nfse_document_number import (
    NfseDocumentNumberError,
    operational_nfse_number,
)
from financial_app.domain.received_fiscal_document import ReceivedFiscalDocument, ReceivedFiscalPage
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.xml.nfse_standard_xml import assert_plausible_xml

_LIST_PATH = "/cliente/nfse/listed"
_XML_SIZE_ERROR = "O XML da NFS-e excede o tamanho máximo permitido."
_SORT_COLUMNS = (
    "NumberNfse",
    "EmissionDate",
    "LiquidValue",
    "CityHall",
    "Status",
)


class QuestorNfseAdapter:
    def __init__(self, session: QuestorCompanySession) -> None:
        self._session = session

    def list_received_nfse(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage:
        payload = self._session.get_json("nfse.list", _LIST_PATH, self._list_params(query))
        items: list[ReceivedFiscalDocument] = []
        for row in payload.get("aaData") or []:
            if isinstance(row, dict):
                mapped = self._map_item(row)
                if mapped is not None:
                    items.append(mapped)
        total = _as_int(
            payload.get("iTotalDisplayRecords"),
            _as_int(payload.get("iTotalRecords"), len(items)),
        )
        return ReceivedFiscalPage(total_items=total, items=tuple(items))

    def download_xml(self, *, document_id: str, variant: str) -> bytes:
        kind = _xml_variant(variant)
        path = f"/cliente/nfse/{document_id}/download-xml-{kind}"
        operation = f"nfse.xml_{kind}"
        status, body = self._session.get_bytes(operation, path, {}, size_error=_XML_SIZE_ERROR)
        if _xml_needs_reauth(status, body):
            self._session.force_reauthenticate()
            status, body = self._session.get_bytes(operation, path, {}, size_error=_XML_SIZE_ERROR)
            if _xml_needs_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        _validate_xml_download(status, body, self._session.max_bytes)
        return body

    def _list_params(self, query: ReceivedInvoiceQuery) -> dict[str, str]:
        start = (query.page - 1) * query.page_size
        emission_index = _SORT_COLUMNS.index("EmissionDate")
        params = {
            "Entry": "True",
            "sEcho": "1",
            "iDisplayStart": str(start),
            "iDisplayLength": str(query.page_size),
            "iSortCol_0": str(emission_index),
            "sSortDir_0": "desc",
        }
        for index, column in enumerate(_SORT_COLUMNS):
            params[f"mDataProp_{index}"] = column
        if query.invoice_number:
            params["Number"] = query.invoice_number
        cnpj = _digits(query.supplier_cnpj)
        if cnpj:
            params["SearchCnpj"] = cnpj
        if query.amount is not None:
            rendered = _br_decimal(query.amount)
            params["InitialValue"] = rendered
            params["EndValue"] = rendered
        return params

    def _map_item(self, row: dict[str, Any]) -> ReceivedFiscalDocument | None:
        provider = row.get("Provider") if isinstance(row.get("Provider"), dict) else {}
        taker = row.get("Taker") if isinstance(row.get("Taker"), dict) else {}
        provider_number = _text(row.get("NumberNfse"))
        try:
            operational = operational_nfse_number(provider_number)
        except NfseDocumentNumberError:
            return None
        document_id = _text(row.get("Id"))
        amount = _amount_text(row.get("LiquidValue"))
        return ReceivedFiscalDocument(
            document_type="nfse",
            branch_code=self._session.branch_code,
            provider_document_id=document_id,
            provider_document_number=provider_number,
            document_number=operational,
            document_match_key=operational,
            provider_document_key=None,
            series="",
            issuer_name=_text(provider.get("Name")),
            issuer_cnpj=_digits(provider.get("CPFCNPJ")) or None,
            receiver_name=_text(taker.get("Name")),
            receiver_cnpj=_digits(taker.get("CPFCNPJ")) or None,
            emission_at=_emission(row.get("EmissionDate")),
            amount=amount,
            amount_formatted=_format_brl(amount),
            city_hall=_city_hall(row.get("CityHall")) or None,
            printable_available=False,
            xml_original_available=bool(document_id),
            xml_standard_available=bool(document_id),
            provider_status=_text(row.get("Status")),
        )


def _xml_variant(value: str) -> str:
    variant = (value or "").strip().lower().replace("-", "_")
    if variant in {"original", "xml_original"}:
        return "original"
    if variant in {"standard", "xml_standard"}:
        return "standard"
    raise QuestorInvalidResponse("Tipo de XML da NFS-e inválido.")


def _xml_needs_reauth(status: int, body: bytes) -> bool:
    if status in {401, 403}:
        return True
    sample = body.lstrip()[:240].lower()
    return sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head")


def _validate_xml_download(status: int, body: bytes, max_bytes: int) -> None:
    if status == 404:
        raise QuestorDocumentNotFound("XML da NFS-e não encontrado.")
    if status >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if status >= 400:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    assert_plausible_xml(body, max_bytes=max_bytes)
    if not body.lstrip().startswith(b"<"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")


def _br_decimal(amount: Decimal) -> str:
    rendered = format(amount, "f")
    if "." in rendered:
        whole, fraction = rendered.split(".", 1)
        return f"{whole},{fraction}"
    return f"{rendered},00"


def _digits(value: Any) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _amount_text(value: Any) -> str:
    if value is None or value == "" or isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    if isinstance(value, float) or re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        amount = Decimal(str(value) if isinstance(value, float) else text)
        if amount == amount.to_integral():
            return str(amount.to_integral())
        return format(amount, "f")
    return text


def _format_brl(amount: str) -> str:
    if not amount:
        return ""
    try:
        quantized = Decimal(amount)
    except Exception:
        return amount
    rendered = format(quantized, "f")
    if "." in rendered:
        whole, fraction = rendered.split(".", 1)
        fraction = (fraction + "00")[:2]
    else:
        whole, fraction = rendered, "00"
    return f"R$ {whole},{fraction}"


def _emission(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}.*", text):
        day, month, year = text[:10].split("/")
        clock = text[11:].strip()
        iso = f"{year}-{month}-{day}"
        return f"{iso}T{clock}" if clock else iso
    return text


def _city_hall(value: Any) -> str:
    if isinstance(value, dict):
        return _text(value.get("Name") or value.get("Description") or value.get("City"))
    return _text(value)

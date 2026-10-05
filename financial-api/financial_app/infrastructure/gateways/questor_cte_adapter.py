"""CT-e recebido no portal Questor. Usa a sessão HTTP da filial, sem novo login.

Paths identificados no portal, não são API pública versionada:
`GET /cliente/cte/listagem` com `Entry=0`;
`GET /cliente/transferenciaArquivo/download` para o XML;
`GET /cliente/cte/dactevisualizar` para o DACTE.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorUnavailable,
)
from financial_app.domain.fiscal_access_key import (
    access_key_check_digit_ok,
    access_key_model,
    access_key_number,
    access_key_series,
)
from financial_app.domain.received_fiscal_document import ReceivedFiscalDocument, ReceivedFiscalPage
from financial_app.domain.received_invoice import ReceivedInvoiceQuery
from financial_app.infrastructure.gateways.questor_company_session import QuestorCompanySession
from financial_app.infrastructure.xml.nfse_standard_xml import xml_inspection_sample

_LIST_PATH = "/cliente/cte/listagem"
_XML_PATH = "/cliente/transferenciaArquivo/download"
_DACTE_PATH = "/cliente/cte/dactevisualizar"
_HEX_24 = re.compile(r"^[0-9a-fA-F]{24}$")
_XML_SIZE_ERROR = "O XML do CT-e excede o tamanho máximo permitido."
_PDF_SIZE_ERROR = "O DACTE excede o tamanho máximo permitido."


class QuestorCteAdapter:
    def __init__(self, session: QuestorCompanySession) -> None:
        self._session = session

    def list_received_cte(self, query: ReceivedInvoiceQuery) -> ReceivedFiscalPage:
        payload = self._session.get_json("cte.list", _LIST_PATH, self._list_params(query))
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

    def download_cte_xml(self, *, provider_file_id: str, provider_document_id: str) -> bytes:
        params = {
            "Id": _hex24(provider_file_id, "Identificador do arquivo do CT-e inválido."),
            "IdEntity": _hex24(provider_document_id, "Identificador do CT-e inválido."),
        }
        status, body = self._session.get_bytes("cte.xml", _XML_PATH, params, size_error=_XML_SIZE_ERROR)
        if _xml_needs_reauth(status, body):
            self._session.force_reauthenticate()
            status, body = self._session.get_bytes("cte.xml", _XML_PATH, params, size_error=_XML_SIZE_ERROR)
            if _xml_needs_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        _validate_xml(status, body, self._session.max_bytes)
        return body

    def download_dacte(
        self,
        *,
        provider_file_id: str,
        provider_document_id: str,
        access_key: str,
    ) -> bytes:
        key = _cte_key(access_key)
        params = {
            "Id": _hex24(provider_file_id, "Identificador do arquivo do CT-e inválido."),
            "IdEntity": _hex24(provider_document_id, "Identificador do CT-e inválido."),
            "number": key,
        }
        status, body = self._session.get_bytes("cte.dacte", _DACTE_PATH, params, size_error=_PDF_SIZE_ERROR)
        if _pdf_needs_reauth(status, body):
            self._session.force_reauthenticate()
            status, body = self._session.get_bytes("cte.dacte", _DACTE_PATH, params, size_error=_PDF_SIZE_ERROR)
            if _pdf_needs_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        return _validate_pdf(status, body)

    def _list_params(self, query: ReceivedInvoiceQuery) -> dict[str, str]:
        start = (query.page - 1) * query.page_size
        params = {
            "Entry": "0",
            "orderGroup": "DhEmi",
            "sEcho": "1",
            "iDisplayStart": str(start),
            "iDisplayLength": str(query.page_size),
            "NumberCte": query.invoice_number or "",
            "Serie": "",
            "KeyCte": "",
            "ValueOf": "",
            "ToValue": "",
            "EmissionStart": "",
            "EmissionEnd": "",
            "DateentryStart": "",
            "DateentryEnd": "",
        }
        if query.amount is not None:
            rendered = _br_decimal(query.amount)
            params["ValueOf"] = rendered
            params["ToValue"] = rendered
        return params

    def _map_item(self, row: dict[str, Any]) -> ReceivedFiscalDocument | None:
        cte_key = row.get("CteKey") if isinstance(row.get("CteKey"), dict) else {}
        document_id = _text(row.get("Id"))
        file_id = _text(row.get("XmlFilename"))
        access_key = _digits(_text(row.get("Key")))
        if not _HEX_24.fullmatch(document_id) or len(access_key) != 44:
            return None
        if access_key_model(access_key) != "57" or not access_key_check_digit_ok(access_key):
            return None
        number = _nine_digits(_text(cte_key.get("NCte")) or access_key_number(access_key))
        series = _three_digits(_text(cte_key.get("Serie")) or _text(row.get("Serie")) or access_key_series(access_key))
        issuer_cnpj = _digits(_text(cte_key.get("Cnpj"))) or access_key[6:20]
        if not number or not series or len(issuer_cnpj) != 14:
            return None
        amount = _amount_text(row.get("VtPrest"))
        return ReceivedFiscalDocument(
            document_type="cte",
            branch_code=self._session.branch_code,
            provider_document_id=document_id,
            provider_document_number=number,
            document_number=number,
            document_match_key=number,
            provider_document_key=access_key,
            series=series,
            issuer_name=_text(row.get("TakerName")),
            issuer_cnpj=issuer_cnpj,
            receiver_name="",
            receiver_cnpj=None,
            emission_at=_text(row.get("DhEmi")) or None,
            amount=amount,
            amount_formatted=_text(row.get("ValueFormated")),
            city_hall=None,
            printable_available=_flag(row.get("XmlDacte")),
            xml_original_available=bool(_HEX_24.fullmatch(file_id)),
            xml_standard_available=False,
            access_key=access_key,
            manifestation_code=_text(row.get("Manifestation")),
            manifestation_description=_text(row.get("ManifestationDescription")),
            provider_file_id=file_id or None,
        )


def _hex24(value: str, message: str) -> str:
    text = (value or "").strip()
    if not _HEX_24.fullmatch(text):
        raise QuestorInvalidResponse(message)
    return text


def _cte_key(value: str) -> str:
    digits = _digits(value)
    if len(digits) != 44 or access_key_model(digits) != "57" or not access_key_check_digit_ok(digits):
        raise QuestorInvalidResponse("Chave de acesso do CT-e inválida.")
    return digits


def _xml_needs_reauth(status: int, body: bytes) -> bool:
    if status in {401, 403}:
        return True
    sample = xml_inspection_sample(body)[:240].lower()
    return sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head")


def _validate_xml(status: int, body: bytes, max_bytes: int) -> None:
    if status == 404:
        raise QuestorDocumentNotFound("XML do CT-e não encontrado.")
    if status >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if status >= 400 or len(body) > max_bytes:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    sample = xml_inspection_sample(body)
    if not sample.startswith(b"<"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    folded = body.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise QuestorInvalidResponse("O XML do CT-e foi recusado por segurança.")


def _pdf_needs_reauth(status: int, body: bytes) -> bool:
    if status in {401, 403}:
        return True
    if body.lstrip().startswith(b"%PDF"):
        return False
    sample = body.lstrip()[:240].lower()
    return sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head")


def _validate_pdf(status: int, body: bytes) -> bytes:
    if status == 404:
        raise QuestorDocumentNotFound("DACTE não encontrado para este CT-e.")
    if status >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if status >= 400 or not body.startswith(b"%PDF"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    return body


def _nine_digits(value: str) -> str:
    digits = _digits(value)
    if not digits or len(digits) > 9:
        return ""
    return digits.zfill(9)


def _three_digits(value: str) -> str:
    digits = _digits(value)
    if not digits or len(digits) > 3:
        return ""
    return digits.zfill(3)


def _br_decimal(amount: Decimal) -> str:
    rendered = format(amount, "f")
    if "." in rendered:
        whole, fraction = rendered.split(".", 1)
        return f"{whole},{fraction}"
    return f"{rendered},00"


def _amount_text(value: Any) -> str:
    text = _text(value).replace("R$", "").replace(" ", "")
    if not text:
        return ""
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return format(Decimal(text), "f")
    except (InvalidOperation, ValueError):
        return ""


def _as_int(value: Any, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).lower()
    return text not in {"", "0", "false", "n", "no", "nao", "não"}


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

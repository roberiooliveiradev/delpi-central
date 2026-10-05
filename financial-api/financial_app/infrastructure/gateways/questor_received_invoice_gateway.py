"""Adapter do portal Questor Zen para NF-e de entrada, DANFE e XML.

Os paths abaixo foram identificados no portal, não numa API pública versionada:

- `GET /cliente/nfe/listagem`
- `GET /cliente/nfe/pegarpdfdenfe`
- `GET /cliente/transferenciaArquivo/download` (XML; Id=XmlFilename, IdEntity=row.Id)

A sessão HTTP é da filial e pode ser compartilhada com a NFS-e e o CT-e.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Callable

import httpx

from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorUnavailable,
)
from financial_app.domain.nfe_export import NfeExportListingPage, QuestorNfeListing
from financial_app.domain.received_invoice import (
    ReceivedInvoice,
    ReceivedInvoicePage,
    ReceivedInvoiceQuery,
)
from financial_app.infrastructure.gateways.questor_company_session import (
    QuestorCompanySession,
    _QuestorLogRedactionFilter,
)
from financial_app.infrastructure.xml.nfse_standard_xml import xml_inspection_sample

_LIST_PATH = "/cliente/nfe/listagem"
_DANFE_PATH = "/cliente/nfe/pegarpdfdenfe/"
_XML_PATH = "/cliente/transferenciaArquivo/download"
_DANFE_SIZE_ERROR = "O DANFE excede o tamanho máximo permitido."
_XML_SIZE_ERROR = "O XML da NF-e excede o tamanho máximo permitido."
_HEX_24 = re.compile(r"^[0-9a-fA-F]{24}$")
_ISSUER_CNPJ_KEYS = (
    "IssuerFederalRegistration",
    "IssuerCnpj",
    "IssuerCNPJ",
    "FederalRegistration",
)


class QuestorReceivedInvoiceGateway:
    def __init__(
        self,
        *,
        branch_code: str = "",
        company_id: str | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        timeout_seconds: float | None = None,
        danfe_max_bytes: int | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] | None = None,
        session: QuestorCompanySession | None = None,
    ) -> None:
        if session is not None:
            self._session = session
            self._owns_session = False
        else:
            self._session = QuestorCompanySession(
                branch_code=branch_code,
                company_id=company_id,
                base_url=base_url,
                api_token=api_token,
                timeout_seconds=timeout_seconds,
                max_bytes=danfe_max_bytes,
                client=client,
                sleeper=sleeper,
            )
            self._owns_session = True

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def list_received_invoices(self, query: ReceivedInvoiceQuery) -> ReceivedInvoicePage:
        params = self._list_params(query)
        payload = self._session.get_json("list_received_invoices", _LIST_PATH, params)
        items = tuple(
            self._map_item(row) for row in payload.get("aaData") or [] if isinstance(row, dict)
        )
        total = _as_int(
            payload.get("iTotalDisplayRecords"),
            _as_int(payload.get("iTotalRecords"), len(items)),
        )
        return ReceivedInvoicePage(total_items=total, items=items)

    def download_danfe(self, *, document_id: str, access_key: str) -> bytes:
        params = {"Id": document_id, "chNFe": access_key}
        status, body = self._session.get_bytes(
            "download_danfe",
            _DANFE_PATH,
            params,
            size_error=_DANFE_SIZE_ERROR,
        )
        if _bytes_need_reauth(status, body):
            self._session.force_reauthenticate()
            status, body = self._session.get_bytes(
                "download_danfe",
                _DANFE_PATH,
                params,
                size_error=_DANFE_SIZE_ERROR,
            )
            if _bytes_need_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        return _validate_pdf(status, body)

    def list_nfe_export_page(self, query: ReceivedInvoiceQuery) -> NfeExportListingPage:
        """Listagem NF-e para exportação. Preserva row.Id e XmlFilename."""

        payload = self._session.get_json("nfe.list", _LIST_PATH, self._list_params(query))
        items = tuple(
            self._map_export_row(row)
            for row in payload.get("aaData") or []
            if isinstance(row, dict)
        )
        total = _as_int(
            payload.get("iTotalDisplayRecords"),
            _as_int(payload.get("iTotalRecords"), len(items)),
        )
        return NfeExportListingPage(total_items=total, items=items)

    def download_nfe_xml(self, *, provider_file_id: str, provider_document_id: str) -> bytes:
        """Baixa o XML da NF-e na sessão da filial.

        Id é o XmlFilename. IdEntity é o Id da linha. Os dois não se substituem.
        """

        params = {
            "Id": _hex24(provider_file_id, "Identificador do arquivo da NF-e inválido."),
            "IdEntity": _hex24(provider_document_id, "Identificador da NF-e inválido."),
        }
        status, body = self._session.get_bytes(
            "nfe.xml",
            _XML_PATH,
            params,
            size_error=_XML_SIZE_ERROR,
        )
        if _xml_needs_reauth(status, body):
            self._session.force_reauthenticate()
            status, body = self._session.get_bytes(
                "nfe.xml",
                _XML_PATH,
                params,
                size_error=_XML_SIZE_ERROR,
            )
            if _xml_needs_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        _validate_nfe_xml_payload(status, body, self._session.max_bytes)
        return body

    @property
    def branch_code(self) -> str:
        return self._session.branch_code

    def _http(self) -> httpx.Client:
        return self._session.http()

    def _list_params(self, query: ReceivedInvoiceQuery) -> dict[str, str]:
        start = (query.page - 1) * query.page_size
        params = {
            "type": "NFe-0",
            "orderGroup": "Emission",
            "sEcho": "1",
            "iDisplayStart": str(start),
            "iDisplayLength": str(query.page_size),
            "Entry": "True",
        }
        if query.invoice_number:
            params["NfeNumber"] = query.invoice_number
        cnpj = _digits(query.supplier_cnpj)
        if cnpj:
            params["IssuerFederalRegistration"] = cnpj
        params.update(_exact_amount_query(query.amount))
        return params

    def _map_item(self, row: dict[str, Any]) -> ReceivedInvoice:
        # XmlFilename é o Id do DANFE. O campo Id é outro identificador interno.
        return ReceivedInvoice(
            document_id=_text(row.get("XmlFilename")),
            access_key=_text(row.get("Number")),
            invoice_number=_text(row.get("NfeNumber")),
            series=_text(row.get("Serie")),
            issuer_name=_text(row.get("Issuer")),
            issuer_cnpj=_issuer_cnpj(row),
            receiver_name=_text(row.get("Receiver")),
            emission_at=_text(row.get("Emission")) or None,
            amount=_amount_text(row.get("Value")),
            amount_formatted=_text(row.get("ValueFormated")),
            manifestation_code=_text(row.get("Manifestation")),
            manifestation_description=_text(row.get("ManifestationDescription")),
            danfe_available=_flag(row.get("XmlDanfe")),
            branch_code=self._session.branch_code,
        )

    def _map_export_row(self, row: dict[str, Any]) -> QuestorNfeListing:
        return QuestorNfeListing(
            provider_file_id=_text(row.get("XmlFilename")),
            provider_entity_id=_text(row.get("Id")),
            access_key=_text(row.get("Number")),
            invoice_number=_text(row.get("NfeNumber")),
            series=_text(row.get("Serie")),
            issuer_cnpj=_issuer_cnpj(row),
            emission_at=_text(row.get("Emission")) or None,
            branch_code=self._session.branch_code,
        )


def _exact_amount_query(amount: Decimal | None) -> dict[str, str]:
    """Valor exato vira o intervalo fechado ValueOf..ToValue, em formato brasileiro.

    Prova live no portal alliance em 2026-10-01:
    ValueOf é o mínimo e ToValue é o máximo; o ponto é separador de milhar
    (108.00 foi interpretado como 10800); o parâmetro Value não limita o intervalo.
    """

    if amount is None:
        return {}
    rendered = format(amount, "f")
    if "." in rendered:
        whole, fraction = rendered.split(".", 1)
        rendered = f"{whole},{fraction}"
    else:
        rendered = f"{rendered},00"
    return {"ValueOf": rendered, "ToValue": rendered}


def _explicit_timeout(total_seconds: float) -> httpx.Timeout:
    bounded = max(total_seconds, 0.1)
    short = min(_CONNECT_TIMEOUT_CAP_SECONDS, bounded)
    return httpx.Timeout(connect=short, read=bounded, write=short, pool=short)


def _retry_after_seconds(response: httpx.Response | None) -> float | None:
    if response is None:
        return None
    raw = (response.headers.get("retry-after") or "").strip()
    if not raw or not raw.isdigit():
        return None
    return float(raw)


def _response_needs_reauth(response: httpx.Response) -> bool:
    if response.status_code in {401, 403}:
        return True
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" in content_type or "application/xhtml" in content_type:
        return True
    if response.status_code == 200 and "json" not in content_type:
        sample = response.content[:64].lstrip().lower()
        if sample.startswith(b"<"):
            return True
    return False


def _bytes_need_reauth(status: int, body: bytes) -> bool:
    if status in {401, 403}:
        return True
    if body.lstrip().startswith(b"%PDF"):
        return False
    sample = body.lstrip()[:240].lower()
    return sample.startswith(b"<") or sample.startswith(b"<!doctype")


def _parse_list_payload(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 404:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if response.status_code >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if response.status_code >= 400:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    try:
        payload = response.json()
    except ValueError:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if not isinstance(payload, dict) or not isinstance(payload.get("aaData"), list):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    return payload


def _hex24(value: str, message: str) -> str:
    text = (value or "").strip()
    if not _HEX_24.fullmatch(text):
        raise QuestorInvalidResponse(message)
    return text


def _xml_needs_reauth(status: int, body: bytes) -> bool:
    if status in {401, 403}:
        return True
    sample = xml_inspection_sample(body)[:240].lower()
    return sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"<head")


def _validate_nfe_xml_payload(status: int, body: bytes, max_bytes: int) -> None:
    if status == 404:
        raise QuestorDocumentNotFound("XML da NF-e não encontrado.")
    if status >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if status >= 400 or len(body) > max_bytes:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    sample = xml_inspection_sample(body)
    if not sample.startswith(b"<"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    folded = body.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise QuestorInvalidResponse("O XML da NF-e foi recusado por segurança.")


def _validate_pdf(status: int, body: bytes) -> bytes:
    if status == 404:
        raise QuestorDocumentNotFound("DANFE não encontrado para esta nota.")
    if status >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if status >= 400 or not body.startswith(b"%PDF"):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    return body


def _digits(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
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


def _issuer_cnpj(row: dict[str, Any]) -> str | None:
    explicit = _explicit_issuer_cnpj(row)
    if explicit:
        return explicit
    return _cnpj_from_access_key(_text(row.get("Number")))


def _explicit_issuer_cnpj(row: dict[str, Any]) -> str | None:
    for key in _ISSUER_CNPJ_KEYS:
        if key not in row or row.get(key) in (None, ""):
            continue
        digits = _digits(_text(row.get(key)))
        return digits or _text(row.get(key)) or None
    return None


def _cnpj_from_access_key(access_key: str) -> str | None:
    """O CNPJ do emitente ocupa as posições 7 a 20 da chave da NF-e modelo 55.

    A listagem do portal Questor não devolve esse campo. A chave válida traz
    o CNPJ sem consultar outro endpoint. O dígito verificador mora em
    `fiscal_access_key` e também vale para o CT-e modelo 57.
    """
    from financial_app.domain.fiscal_access_key import (
        access_key_check_digit_ok,
        access_key_cnpj,
        access_key_model,
    )

    digits = _digits(access_key)
    if len(digits) != 44 or access_key_model(digits) != "55" or not access_key_check_digit_ok(digits):
        return None
    return access_key_cnpj(digits)


def _access_key_check_digit_ok(digits: str) -> bool:
    from financial_app.domain.fiscal_access_key import access_key_check_digit_ok

    return access_key_check_digit_ok(digits)


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = _text(value).lower()
    if text in {"", "0", "false", "n", "no", "nao", "não"}:
        return False
    return True

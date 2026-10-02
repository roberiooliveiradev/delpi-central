"""Adapter do portal Questor Zen para NF-e de entrada e DANFE.

Os paths `/cliente/nfe/listagem` e `/cliente/nfe/pegarpdfdenfe` foram
identificados no portal, não numa API pública versionada. A sessão HTTP é
da filial e pode ser compartilhada com a NFS-e.
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
from financial_app.domain.received_invoice import (
    ReceivedInvoice,
    ReceivedInvoicePage,
    ReceivedInvoiceQuery,
)
from financial_app.infrastructure.gateways.questor_company_session import (
    QuestorCompanySession,
    _QuestorLogRedactionFilter,
)

_LIST_PATH = "/cliente/nfe/listagem"
_DANFE_PATH = "/cliente/nfe/pegarpdfdenfe/"
_DANFE_SIZE_ERROR = "O DANFE excede o tamanho máximo permitido."
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
    o CNPJ sem consultar outro endpoint.
    """
    digits = _digits(access_key)
    if len(digits) != 44 or digits[20:22] != "55" or not _access_key_check_digit_ok(digits):
        return None
    return digits[6:20]


def _access_key_check_digit_ok(digits: str) -> bool:
    weights = (2, 3, 4, 5, 6, 7, 8, 9)
    total = sum(int(digit) * weights[index % 8] for index, digit in enumerate(reversed(digits[:43])))
    remainder = total % 11
    expected = 0 if remainder < 2 else 11 - remainder
    return digits[43] == str(expected)


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = _text(value).lower()
    if text in {"", "0", "false", "n", "no", "nao", "não"}:
        return False
    return True

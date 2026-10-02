"""Adapter do portal Questor Zen para NF-e de entrada e DANFE.

Os paths `/cliente/nfe/listagem` e `/cliente/nfe/pegarpdfdenfe` foram
identificados no portal, não numa API pública versionada. A sessão usa o
token só no backend, em query string, porque esse é o contrato do Questor.
Nenhuma URL, cookie ou token entra em log ou em mensagem de erro.
"""

from __future__ import annotations

import logging
import random
import re
import threading
import time
from decimal import Decimal
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from financial_app.config import settings
from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorDocumentNotFound,
    QuestorInvalidResponse,
    QuestorNotConfigured,
    QuestorUnavailable,
)
from financial_app.domain.received_invoice import (
    ReceivedInvoice,
    ReceivedInvoicePage,
    ReceivedInvoiceQuery,
)

logger = logging.getLogger(__name__)

_LIST_PATH = "/cliente/nfe/listagem"
_DANFE_PATH = "/cliente/nfe/pegarpdfdenfe/"
_AUTH_PATH = "/entrarcomtoken"
_SWITCH_COMPANY_PATH = "/trocarempresa"
_AUTHORIZE_PATH = "/autorizar"
# O nginx do portal responde 403 ao User-Agent padrão do httpx e aceita um
# identificador próprio da aplicação. Comprovado em 2026-10-01 no host alliance.
_USER_AGENT = "MinhaDELPI-FinancialAPI/1.0"
_TRANSIENT_STATUSES = frozenset({408, 429, 502, 503, 504})
_MAX_GET_ATTEMPTS = 3
_RETRY_AFTER_CAP_SECONDS = 2.0
_CONNECT_TIMEOUT_CAP_SECONDS = 10.0
_ISSUER_CNPJ_KEYS = (
    "IssuerFederalRegistration",
    "IssuerCnpj",
    "IssuerCNPJ",
    "FederalRegistration",
)
_LOG_REDACTION_INSTALLED = False


class _QuestorLogRedactionFilter(logging.Filter):
    """Descarta linhas que possam carregar o token da query ou o cookie jar."""

    _MARKERS = ("entrarcomtoken", "token=", "asp.net_sessionid", ".appname")

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage().lower()
        except Exception:
            return False
        return not any(marker in rendered for marker in self._MARKERS)


def install_questor_log_redaction() -> None:
    """O httpx registra a URL no nível INFO. O token iria junto na query."""

    global _LOG_REDACTION_INSTALLED
    if _LOG_REDACTION_INSTALLED:
        return
    redactor = _QuestorLogRedactionFilter()
    for name in ("httpx", "httpcore"):
        provider_logger = logging.getLogger(name)
        provider_logger.addFilter(redactor)
        if provider_logger.level == logging.NOTSET or provider_logger.level < logging.WARNING:
            provider_logger.setLevel(logging.WARNING)
    _LOG_REDACTION_INSTALLED = True


install_questor_log_redaction()


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
    ) -> None:
        install_questor_log_redaction()
        configured_base = (base_url if base_url is not None else settings.FIN_QUESTOR_BASE_URL).rstrip("/")
        self._base_url = configured_base
        self._allowed_host = (urlparse(configured_base).hostname or "").lower()
        self._branch_code = (branch_code or "").strip()
        self._company_id = None if company_id is None else company_id.strip()
        self._api_token = api_token
        self._timeout_seconds = float(
            timeout_seconds if timeout_seconds is not None else settings.FIN_QUESTOR_TIMEOUT_SECONDS
        )
        self._danfe_max_bytes = int(
            danfe_max_bytes if danfe_max_bytes is not None else settings.FIN_QUESTOR_DANFE_MAX_BYTES
        )
        self._client = client
        self._owns_client = client is None
        if client is not None:
            hooks = client.event_hooks.setdefault("response", [])
            if self._reject_foreign_host not in hooks:
                hooks.append(self._reject_foreign_host)
        self._sleeper = sleeper or time.sleep
        self._authenticated = False
        self._auth_lock = threading.Lock()

    def close(self) -> None:
        client = self._client
        self._client = None
        self._authenticated = False
        if client is not None and self._owns_client and not client.is_closed:
            client.close()

    def list_received_invoices(self, query: ReceivedInvoiceQuery) -> ReceivedInvoicePage:
        params = self._list_params(query)
        payload = self._json_with_session("list_received_invoices", _LIST_PATH, params)
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
        self._ensure_authenticated()
        status, body = self._get_bytes("download_danfe", _DANFE_PATH, params)
        if _bytes_need_reauth(status, body):
            self._force_reauthenticate()
            status, body = self._get_bytes("download_danfe", _DANFE_PATH, params)
            if _bytes_need_reauth(status, body):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        return _validate_pdf(status, body)

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

    def _json_with_session(self, operation: str, path: str, params: dict[str, str]) -> dict[str, Any]:
        self._ensure_authenticated()
        response = self._get(operation, path, params)
        if _response_needs_reauth(response):
            self._force_reauthenticate()
            response = self._get(operation, path, params)
            if _response_needs_reauth(response):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        return _parse_list_payload(response)

    def _ensure_authenticated(self) -> None:
        if self._authenticated:
            return
        with self._auth_lock:
            if self._authenticated:
                return
            self._authenticate()

    def _force_reauthenticate(self) -> None:
        with self._auth_lock:
            self._authenticated = False
            self._authenticate()

    def _authenticate(self) -> None:
        credential = self._resolved_token()
        if not credential:
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
        company_id = self._resolved_company_id()
        if not company_id:
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
        response = self._get("authenticate", _AUTH_PATH, {"token": credential})
        if response.status_code >= 400 or not self._has_session_cookie():
            self._authenticated = False
            raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        self._select_company(company_id)
        self._authenticated = True

    def _resolved_company_id(self) -> str:
        return (self._company_id or "").strip()

    def _select_company(self, company_id: str) -> None:
        """A empresa ativa é o cookie da sessão. Cada gateway fica preso à sua."""

        response = self._post_form(
            "select_company",
            _SWITCH_COMPANY_PATH,
            {"CompanyId": company_id},
        )
        if response.status_code in _TRANSIENT_STATUSES:
            self._authenticated = False
            raise QuestorUnavailable("Não foi possível consultar todas as empresas no Questor Zen.")
        if response.status_code >= 400:
            self._authenticated = False
            raise QuestorAuthenticationError("Não foi possível selecionar a empresa no Questor Zen.")
        authorized = self._get("authorize_company", _AUTHORIZE_PATH, {})
        if authorized.status_code >= 400 or not self._has_session_cookie():
            self._authenticated = False
            raise QuestorAuthenticationError("Não foi possível selecionar a empresa no Questor Zen.")

    def _post_form(self, operation: str, path: str, form: dict[str, str]) -> httpx.Response:
        started = time.perf_counter()
        try:
            response = self._http().post(path, data=form)
        except httpx.TimeoutException:
            self._log(operation, "timeout", 1, started)
            raise QuestorUnavailable("Não foi possível consultar todas as empresas no Questor Zen.")
        except httpx.HTTPError:
            self._log(operation, "error", 1, started)
            raise QuestorUnavailable("Não foi possível consultar todas as empresas no Questor Zen.")
        self._log(operation, str(response.status_code), 1, started)
        return response

    def _resolved_token(self) -> str:
        if self._api_token is None:
            raw = settings.FIN_QUESTOR_API_TOKEN
        else:
            raw = self._api_token
        return (raw or "").strip()

    def _has_session_cookie(self) -> bool:
        names = {cookie.name for cookie in self._http().cookies.jar}
        return "ASP.NET_SessionId" in names or ".APPNAME" in names

    def _get(self, operation: str, path: str, params: dict[str, str]) -> httpx.Response:
        for attempt in range(1, _MAX_GET_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                response = self._http().get(path, params=params)
            except httpx.TimeoutException:
                self._log(operation, "timeout", attempt, started)
                if attempt >= _MAX_GET_ATTEMPTS:
                    raise QuestorUnavailable("A consulta ao Questor excedeu o tempo limite.")
                self._sleep_before_retry(attempt, None)
                continue
            except httpx.HTTPError:
                self._log(operation, "error", attempt, started)
                if attempt >= _MAX_GET_ATTEMPTS:
                    raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
                self._sleep_before_retry(attempt, None)
                continue
            self._log(operation, str(response.status_code), attempt, started)
            if response.status_code in _TRANSIENT_STATUSES and attempt < _MAX_GET_ATTEMPTS:
                self._sleep_before_retry(attempt, response)
                continue
            if response.status_code in _TRANSIENT_STATUSES:
                raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
            return response
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")

    def _get_bytes(self, operation: str, path: str, params: dict[str, str]) -> tuple[int, bytes]:
        for attempt in range(1, _MAX_GET_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                with self._http().stream("GET", path, params=params) as response:
                    status = response.status_code
                    self._log(operation, str(status), attempt, started)
                    if status in _TRANSIENT_STATUSES and attempt < _MAX_GET_ATTEMPTS:
                        self._sleep_before_retry(attempt, response)
                        continue
                    if status in _TRANSIENT_STATUSES:
                        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
                    return status, self._read_limited(response)
            except (QuestorInvalidResponse, QuestorUnavailable):
                raise
            except httpx.TimeoutException:
                self._log(operation, "timeout", attempt, started)
                if attempt >= _MAX_GET_ATTEMPTS:
                    raise QuestorUnavailable("A consulta ao Questor excedeu o tempo limite.")
                self._sleep_before_retry(attempt, None)
            except httpx.HTTPError:
                self._log(operation, "error", attempt, started)
                if attempt >= _MAX_GET_ATTEMPTS:
                    raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
                self._sleep_before_retry(attempt, None)
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")

    def _read_limited(self, response: httpx.Response) -> bytes:
        declared = response.headers.get("content-length")
        if declared not in (None, ""):
            try:
                size = int(declared)
            except ValueError:
                raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
            if size > self._danfe_max_bytes:
                raise QuestorInvalidResponse("O DANFE excede o tamanho máximo permitido.")
        payload = bytearray()
        for chunk in response.iter_bytes():
            payload.extend(chunk)
            if len(payload) > self._danfe_max_bytes:
                raise QuestorInvalidResponse("O DANFE excede o tamanho máximo permitido.")
        return bytes(payload)

    def _sleep_before_retry(self, attempt: int, response: httpx.Response | None) -> None:
        retry_after = _retry_after_seconds(response)
        if retry_after is not None:
            delay = min(max(retry_after, 0.0), _RETRY_AFTER_CAP_SECONDS)
        else:
            delay = min(0.2 * (2 ** (attempt - 1)), _RETRY_AFTER_CAP_SECONDS)
        delay += random.uniform(0, 0.05)
        self._sleeper(delay)

    def _http(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=_explicit_timeout(self._timeout_seconds),
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                headers={"User-Agent": _USER_AGENT},
                event_hooks={"response": [self._reject_foreign_host]},
            )
            self._owns_client = True
        return self._client

    def _reject_foreign_host(self, response: httpx.Response) -> None:
        host = (response.url.host or "").lower()
        if not self._allowed_host or host != self._allowed_host:
            raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")

    def _log(self, operation: str, status: str, attempt: int, started: float) -> None:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "provider=questor operation=%s branch=%s status=%s duration_ms=%s attempt=%s",
            operation,
            self._branch_code or "-",
            status,
            duration_ms,
            attempt,
        )

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
            branch_code=self._branch_code,
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

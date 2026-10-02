"""Sessão HTTP do Questor Zen por filial.

Login, CompanyId, cookies, retry e reautenticação pertencem à empresa.
NF-e e NFS-e reutilizam o mesmo cliente. O token não entra em log.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from financial_app.config import settings
from financial_app.domain.errors import (
    QuestorAuthenticationError,
    QuestorInvalidResponse,
    QuestorNotConfigured,
    QuestorUnavailable,
)

logger = logging.getLogger(__name__)

_AUTH_PATH = "/entrarcomtoken"
_SWITCH_COMPANY_PATH = "/trocarempresa"
_AUTHORIZE_PATH = "/autorizar"
_USER_AGENT = "MinhaDELPI-FinancialAPI/1.0"
_TRANSIENT_STATUSES = frozenset({408, 429, 502, 503, 504})
_MAX_GET_ATTEMPTS = 3
_RETRY_AFTER_CAP_SECONDS = 2.0
_CONNECT_TIMEOUT_CAP_SECONDS = 10.0
_LOG_REDACTION_INSTALLED = False
_DEFAULT_SIZE_ERROR = "O arquivo excede o tamanho máximo permitido."


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


class QuestorCompanySession:
    def __init__(
        self,
        *,
        branch_code: str = "",
        company_id: str | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        timeout_seconds: float | None = None,
        max_bytes: int | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        install_questor_log_redaction()
        configured_base = (base_url if base_url is not None else settings.FIN_QUESTOR_BASE_URL).rstrip("/")
        self._base_url = configured_base
        self._allowed_host = (urlparse(configured_base).hostname or "").lower()
        self.branch_code = (branch_code or "").strip()
        self._company_id = None if company_id is None else company_id.strip()
        self._api_token = api_token
        self._timeout_seconds = float(
            timeout_seconds if timeout_seconds is not None else settings.FIN_QUESTOR_TIMEOUT_SECONDS
        )
        self.max_bytes = int(
            max_bytes if max_bytes is not None else settings.FIN_QUESTOR_DANFE_MAX_BYTES
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

    def http(self) -> httpx.Client:
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

    def get_json(self, operation: str, path: str, params: dict[str, str]) -> dict[str, Any]:
        self._ensure_authenticated()
        response = self._get(operation, path, params)
        if _response_needs_reauth(response):
            self.force_reauthenticate()
            response = self._get(operation, path, params)
            if _response_needs_reauth(response):
                raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        return _parse_list_payload(response)

    def get_bytes(
        self,
        operation: str,
        path: str,
        params: dict[str, str],
        *,
        size_error: str = _DEFAULT_SIZE_ERROR,
    ) -> tuple[int, bytes]:
        self._ensure_authenticated()
        for attempt in range(1, _MAX_GET_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                with self.http().stream("GET", path, params=params) as response:
                    status = response.status_code
                    self._log(operation, str(status), attempt, started)
                    if status in _TRANSIENT_STATUSES and attempt < _MAX_GET_ATTEMPTS:
                        self._sleep_before_retry(attempt, response)
                        continue
                    if status in _TRANSIENT_STATUSES:
                        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
                    return status, self._read_limited(response, size_error)
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

    def force_reauthenticate(self) -> None:
        with self._auth_lock:
            self._authenticated = False
            self._authenticate()

    def _ensure_authenticated(self) -> None:
        if self._authenticated:
            return
        with self._auth_lock:
            if self._authenticated:
                return
            self._authenticate()

    def _authenticate(self) -> None:
        credential = self._resolved_token()
        if not credential:
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
        company_id = (self._company_id or "").strip()
        if not company_id:
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
        response = self._get("authenticate", _AUTH_PATH, {"token": credential})
        if response.status_code >= 400 or not self._has_session_cookie():
            self._authenticated = False
            raise QuestorAuthenticationError("Não foi possível autenticar no Questor Zen.")
        self._select_company(company_id)
        self._authenticated = True

    def _select_company(self, company_id: str) -> None:
        response = self._post_form("select_company", _SWITCH_COMPANY_PATH, {"CompanyId": company_id})
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
            response = self.http().post(path, data=form)
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
        names = {cookie.name for cookie in self.http().cookies.jar}
        return "ASP.NET_SessionId" in names or ".APPNAME" in names

    def _get(self, operation: str, path: str, params: dict[str, str]) -> httpx.Response:
        for attempt in range(1, _MAX_GET_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                response = self.http().get(path, params=params)
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

    def _read_limited(self, response: httpx.Response, size_error: str) -> bytes:
        declared = response.headers.get("content-length")
        if declared not in (None, ""):
            try:
                size = int(declared)
            except ValueError as exc:
                raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.") from exc
            if size > self.max_bytes:
                raise QuestorInvalidResponse(size_error)
        payload = bytearray()
        for chunk in response.iter_bytes():
            payload.extend(chunk)
            if len(payload) > self.max_bytes:
                raise QuestorInvalidResponse(size_error)
        return bytes(payload)

    def _sleep_before_retry(self, attempt: int, response: httpx.Response | None) -> None:
        retry_after = _retry_after_seconds(response)
        if retry_after is not None:
            delay = min(max(retry_after, 0.0), _RETRY_AFTER_CAP_SECONDS)
        else:
            delay = min(0.2 * (2 ** (attempt - 1)), _RETRY_AFTER_CAP_SECONDS)
        delay += random.uniform(0, 0.05)
        self._sleeper(delay)

    def _reject_foreign_host(self, response: httpx.Response) -> None:
        host = (response.url.host or "").lower()
        if not self._allowed_host or host != self._allowed_host:
            raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")

    def _log(self, operation: str, status: str, attempt: int, started: float) -> None:
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "provider=questor operation=%s branch=%s status=%s duration_ms=%s attempt=%s",
            operation,
            self.branch_code or "-",
            status,
            duration_ms,
            attempt,
        )


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


def _parse_list_payload(response: httpx.Response) -> dict[str, Any]:
    if response.status_code == 404:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    if response.status_code >= 500:
        raise QuestorUnavailable("Não foi possível consultar o Questor Zen.")
    if response.status_code >= 400:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    try:
        payload = response.json()
    except ValueError as exc:
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("aaData"), list):
        raise QuestorInvalidResponse("O Questor Zen devolveu uma resposta inválida.")
    return payload

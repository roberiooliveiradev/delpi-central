"""HTTP client for TOTVS Protheus REST (OAuth2 password + supplier GET)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable
from urllib.parse import quote

import httpx

from app.application.services.integrations.protheus_secret_redaction import redact_text
from app.config import settings
from app.domain.integrations.protheus_rest import (
    ProtheusAccessToken,
    ProtheusRestConfig,
    ProtheusRestError,
)
from app.utils.logger import log_error, log_info

# Protheus OAuth puts username/password in the query string. httpx INFO logs the
# full request URL — keep those loggers quiet so secrets never hit container logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

_TRANSIENT_STATUS = {408, 429, 502, 503, 504}
_MAX_GET_ATTEMPTS = 3
_SUPPLIER_NOT_FOUND_CODES = {"002", "2"}


class ProtheusRestGateway:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client = client
        self._timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else settings.PROTHEUS_REST_TIMEOUT_SECONDS
        )
        self._sleep = sleep
        self._monotonic = monotonic

    def request_access_token(self, config: ProtheusRestConfig) -> ProtheusAccessToken:
        """POST OAuth2 password grant.

        Protheus requires credentials in the query string (not body). Credentials
        are never logged; only the redacted auth path is written on failure.
        Prefer HTTPS endpoints — cleartext HTTP exposes password-grant to the network.
        """
        params = {
            "grant_type": "password",
            "username": config.username,
            "password": config.password,
        }
        # Log only scheme+host+path (never query).
        safe_auth_target = redact_text(config.auth_url)
        try:
            response = self._send(
                "POST",
                config.auth_url,
                params=params,
                headers={"Accept": "application/json"},
            )
        except ProtheusRestError:
            raise
        except Exception:
            log_error(f"Protheus auth request failed target={safe_auth_target}")
            raise ProtheusRestError(
                "Falha na autenticação técnica com o Protheus.",
                code="PROTHEUS_AUTH_FAILED",
                status_code=502,
            ) from None

        if response.status_code >= 400:
            log_error(
                f"Protheus auth HTTP {response.status_code} target={safe_auth_target}"
            )
            raise ProtheusRestError(
                "Falha na autenticação técnica com o Protheus.",
                code="PROTHEUS_AUTH_FAILED",
                status_code=502,
            )

        payload = _json_payload(response)
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise ProtheusRestError(
                "Falha na autenticação técnica com o Protheus.",
                code="PROTHEUS_AUTH_FAILED",
                status_code=502,
            )
        expires_in = _as_int(payload.get("expires_in"), default=3600)
        token_type = str(payload.get("token_type") or "Bearer").strip() or "Bearer"
        log_info("Protheus OAuth token acquired")
        return ProtheusAccessToken(
            access_token=token,
            expires_in=max(1, expires_in),
            token_type=token_type,
            obtained_at_monotonic=self._monotonic(),
        )

    def get_supplier(
        self,
        config: ProtheusRestConfig,
        *,
        supplier_id: str,
        access_token: str,
    ) -> Any:
        url = f"{config.suppliers_base_url}{quote(supplier_id, safe='')}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        response = self._get_with_retry(url, headers=headers)
        if response.status_code in {401, 403}:
            raise ProtheusRestError(
                "Token Protheus inválido ou expirado.",
                code="PROTHEUS_TOKEN_INVALID",
                status_code=502,
            )
        if response.status_code == 404:
            raise ProtheusRestError(
                "Fornecedor não encontrado no Protheus.",
                code="PROTHEUS_SUPPLIER_NOT_FOUND",
                status_code=404,
                recoverable=False,
            )
        if response.status_code >= 400:
            payload = _json_payload(response)
            if _is_supplier_not_found(response.status_code, payload):
                raise ProtheusRestError(
                    "Fornecedor não encontrado no Protheus.",
                    code="PROTHEUS_SUPPLIER_NOT_FOUND",
                    status_code=404,
                    recoverable=False,
                )
            log_error(
                f"Protheus supplier HTTP {response.status_code} "
                f"url={redact_text(url)}"
            )
            raise ProtheusRestError(
                "Erro inesperado ao consultar fornecedor no Protheus.",
                code="PROTHEUS_UPSTREAM_ERROR",
                status_code=502,
            )

        try:
            return response.json()
        except ValueError:
            raise ProtheusRestError(
                "Resposta inválida do Protheus ao consultar fornecedor.",
                code="PROTHEUS_UPSTREAM_ERROR",
                status_code=502,
            ) from None

    def create_supplier(
        self,
        config: ProtheusRestConfig,
        *,
        body: dict[str, Any],
        access_token: str,
    ) -> dict[str, Any]:
        """POST supplier creation — **no automatic retry** (write may be non-idempotent)."""
        url = config.suppliers_base_url.rstrip("/")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        # Single attempt only — timeout after send is indeterminate; never auto-retry.
        response = self._send("POST", url, headers=headers, json_body=body)
        return _map_supplier_write_response(response, url=url, operation="create")

    def _get_with_retry(self, url: str, *, headers: dict[str, str]) -> httpx.Response:
        last_error: ProtheusRestError | None = None
        for attempt in range(1, _MAX_GET_ATTEMPTS + 1):
            try:
                response = self._send("GET", url, headers=headers)
            except ProtheusRestError as exc:
                last_error = exc
                if attempt == _MAX_GET_ATTEMPTS:
                    raise
                self._sleep(_retry_delay(attempt, None))
                continue
            if response.status_code not in _TRANSIENT_STATUS or attempt == _MAX_GET_ATTEMPTS:
                return response
            self._sleep(_retry_delay(attempt, response))
        if last_error is not None:
            raise last_error
        raise ProtheusRestError(
            "Protheus indisponível.",
            code="PROTHEUS_UNAVAILABLE",
            status_code=503,
        )

    def _send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        timeout = _timeout(self._timeout_seconds)
        try:
            if self._client is not None:
                return self._client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=timeout,
                )
            with httpx.Client(timeout=timeout, follow_redirects=False, verify=True) as client:
                return client.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=timeout,
                )
        except httpx.TimeoutException:
            log_error(f"Protheus timeout method={method} url={redact_text(url)}")
            # Write timeout after send is indeterminate — caller must not auto-retry.
            raise ProtheusRestError(
                "Tempo esgotado ao comunicar com o Protheus. "
                "Se foi uma escrita, o resultado pode estar indeterminado — "
                "não reenvie automaticamente.",
                code="PROTHEUS_TIMEOUT",
                status_code=504,
                recoverable=False,
            ) from None
        except httpx.HTTPError:
            log_error(f"Protheus unavailable method={method} url={redact_text(url)}")
            raise ProtheusRestError(
                "Protheus indisponível.",
                code="PROTHEUS_UNAVAILABLE",
                status_code=503,
            ) from None


def _timeout(total: float) -> httpx.Timeout:
    bounded = max(1.0, total)
    short = min(10.0, bounded)
    return httpx.Timeout(connect=short, read=bounded, write=short, pool=short)


def _retry_delay(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after", "")
        if retry_after.isdigit():
            return min(int(retry_after), 2)
    return min(0.2 * (2 ** (attempt - 1)), 2)


def _json_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_supplier_not_found(status_code: int, payload: dict[str, Any]) -> bool:
    if status_code != 400:
        return False
    code = payload.get("code")
    if code is None:
        code = payload.get("errorCode") or payload.get("error_code")
    token = str(code).strip() if code is not None else ""
    if token in _SUPPLIER_NOT_FOUND_CODES:
        return True
    nested = payload.get("error")
    if isinstance(nested, dict):
        nested_code = str(nested.get("code") or "").strip()
        if nested_code in _SUPPLIER_NOT_FOUND_CODES:
            return True
    return False


def _extract_code_error(payload: dict[str, Any]) -> str:
    for key in ("code_error", "codeError", "code", "error_code", "errorCode"):
        raw = payload.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    nested = payload.get("error")
    if isinstance(nested, dict):
        for key in ("code_error", "code", "error_code"):
            raw = nested.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip()
    return ""


def _extract_error_text(payload: dict[str, Any]) -> str:
    for key in ("error", "message", "detailedMessage", "detailed_message"):
        raw = payload.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, dict):
            nested = raw.get("message") or raw.get("error") or raw.get("text")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return ""


def _map_supplier_write_response(
    response: httpx.Response,
    *,
    url: str,
    operation: str,
) -> dict[str, Any]:
    if response.status_code in {401, 403}:
        raise ProtheusRestError(
            "Token Protheus inválido ou expirado.",
            code="PROTHEUS_TOKEN_INVALID",
            status_code=502,
        )

    payload = _json_payload(response)

    if response.status_code >= 500:
        log_error(
            f"Protheus supplier {operation} HTTP {response.status_code} "
            f"url={redact_text(url)}"
        )
        raise ProtheusRestError(
            "Erro inesperado no Protheus ao gravar fornecedor.",
            code="PROTHEUS_UPSTREAM_ERROR",
            status_code=502,
        )

    if response.status_code >= 400:
        code_error = _extract_code_error(payload)
        error_text = _extract_error_text(payload)
        safe_detail = redact_text(error_text)[:240] if error_text else ""

        if code_error in {"001", "1"}:
            # Same code_error used for invalid ID and invalid JSON — discriminate by text.
            lowered = error_text.lower()
            if "json" in lowered:
                raise ProtheusRestError(
                    "JSON inválido rejeitado pelo Protheus."
                    + (f" Detalhe: {safe_detail}" if safe_detail else ""),
                    code="PROTHEUS_SUPPLIER_WRITE_INVALID_JSON",
                    status_code=400,
                    recoverable=False,
                )
            raise ProtheusRestError(
                "Identificador inválido rejeitado pelo Protheus."
                + (f" Detalhe: {safe_detail}" if safe_detail else ""),
                code="PROTHEUS_SUPPLIER_WRITE_INVALID_ID",
                status_code=400,
                recoverable=False,
            )
        if code_error in {"002", "2"}:
            raise ProtheusRestError(
                "Campos obrigatórios ausentes no Protheus."
                + (f" Detalhe: {safe_detail}" if safe_detail else ""),
                code="PROTHEUS_SUPPLIER_WRITE_REQUIRED_FIELDS",
                status_code=400,
                recoverable=False,
            )
        if code_error in {"003", "3"}:
            # Contract notes literal text may say "alterar" even on create.
            raise ProtheusRestError(
                "Falha na rotina MATA020 ao incluir fornecedor."
                + (f" Detalhe: {safe_detail}" if safe_detail else ""),
                code="PROTHEUS_SUPPLIER_WRITE_MATA020_FAILED",
                status_code=400,
                recoverable=False,
            )

        log_error(
            f"Protheus supplier {operation} HTTP {response.status_code} "
            f"code_error={code_error or '-'} url={redact_text(url)}"
        )
        raise ProtheusRestError(
            "Erro ao gravar fornecedor no Protheus."
            + (f" Detalhe: {safe_detail}" if safe_detail else ""),
            code="PROTHEUS_UPSTREAM_ERROR",
            status_code=502,
        )

    # Success shape is TO_INVENTORY — never invent A2_COD.
    if response.status_code == 204 or not payload:
        return {
            "write_outcome": "accepted_by_upstream",
            "creation_confirmed": False,
            "supplier_code": None,
            "supplier_store": None,
            "upstream": None,
        }

    supplier_code = _pick_first_str(
        payload,
        ("A2_COD", "a2_cod", "supplier_code", "codigo", "code"),
    )
    supplier_store = _pick_first_str(
        payload,
        ("A2_LOJA", "a2_loja", "supplier_store", "loja", "store"),
    )
    nested = payload.get("fornecedor") or payload.get("supplier") or payload.get("data")
    if isinstance(nested, dict):
        supplier_code = supplier_code or _pick_first_str(
            nested, ("A2_COD", "a2_cod", "supplier_code", "codigo", "code")
        )
        supplier_store = supplier_store or _pick_first_str(
            nested, ("A2_LOJA", "a2_loja", "supplier_store", "loja", "store")
        )

    return {
        "write_outcome": "accepted_by_upstream",
        "creation_confirmed": bool(supplier_code and supplier_store),
        "supplier_code": supplier_code,
        "supplier_store": supplier_store,
        "upstream": payload,
    }


def _pick_first_str(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = payload.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return None

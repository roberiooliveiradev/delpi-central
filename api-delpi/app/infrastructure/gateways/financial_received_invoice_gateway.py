"""Cliente HTTP da api-delpi para a financial-api (NF-e de entrada).

O Questor fica só na financial-api. Quem pode buscar a nota é decidido na
api-delpi, pela permissão de criar a solicitação. A chamada seguinte usa o
token de serviço interno e não encaminha o JWT do usuário.
"""
from __future__ import annotations

import time
from typing import Any, Callable
from urllib.parse import quote

import httpx

from app.config import settings
from delpi_auth.service_token import get_internal_service_token

_TRANSIENT_STATUS = {408, 429, 502, 503, 504}
_MAX_ATTEMPTS = 3
_MAX_PDF_BYTES = 10_485_760
_DOCUMENT_ID_LENGTH = 24
_ACCESS_KEY_LENGTH = 44
_BRANCHES = {"01", "02"}


class FinancialReceivedInvoiceGatewayError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class FinancialReceivedInvoiceGateway:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        service_token: str | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._base_url = (base_url or settings.FINANCIAL_API_BASE_URL).rstrip("/")
        self._service_token = service_token
        self._timeout_seconds = float(
            timeout_seconds if timeout_seconds is not None else settings.FINANCIAL_API_TIMEOUT_SECONDS
        )
        self._sleep = sleep

    def list_received_invoices(
        self,
        *,
        authorization: str,
        invoice_number: str | None,
        supplier_cnpj: str | None,
        page: int,
        page_size: int,
        document_type: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if invoice_number:
            params["invoiceNumber"] = invoice_number
        if supplier_cnpj:
            params["supplierCnpj"] = supplier_cnpj
        if document_type:
            params["documentType"] = document_type
        response = self._get("/invoices/received", authorization=authorization, params=params)
        payload = _json_payload(response)
        if response.status_code >= 400 or payload.get("success") is False:
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível consultar as notas fiscais."),
                _mapped_status(response.status_code),
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise FinancialReceivedInvoiceGatewayError(
                "A consulta de notas fiscais retornou um formato inválido.",
                502,
            )
        return data

    def download_danfe(
        self,
        *,
        authorization: str,
        document_id: str,
        access_key: str,
        branch: str,
    ) -> tuple[bytes, str]:
        normalized_id = _document_id(document_id)
        normalized_key = _access_key(access_key)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/danfe",
            authorization=authorization,
            params={"accessKey": normalized_key, "branch": normalized_branch},
        )
        if response.status_code >= 400:
            payload = _json_payload(response)
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível obter o DANFE."),
                _mapped_status(response.status_code),
            )
        content = response.content or b""
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > _MAX_PDF_BYTES:
            raise FinancialReceivedInvoiceGatewayError("O DANFE excede o tamanho permitido.", 502)
        if len(content) > _MAX_PDF_BYTES or not content.startswith(b"%PDF"):
            raise FinancialReceivedInvoiceGatewayError("O DANFE retornado não é um PDF válido.", 502)
        return content, f"NFe-{normalized_key}.pdf"

    def download_nfse_xml(
        self,
        *,
        authorization: str,
        document_id: str,
        variant: str,
        branch: str,
    ) -> tuple[bytes, str]:
        normalized_id = _document_id(document_id)
        kind = _xml_variant(variant)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/xml/{kind}",
            authorization=authorization,
            params={"documentType": "nfse", "branch": normalized_branch},
        )
        if response.status_code >= 400:
            payload = _json_payload(response)
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível obter o XML da NFS-e."),
                _mapped_status(response.status_code),
            )
        content = response.content or b""
        if len(content) > _MAX_PDF_BYTES or not _looks_like_xml(content):
            raise FinancialReceivedInvoiceGatewayError("O XML da NFS-e retornado é inválido.", 502)
        return content, f"NFSe-{normalized_id}-{kind}.xml"

    def get_nfse_detail(
        self,
        *,
        authorization: str,
        document_id: str,
        branch: str,
    ) -> dict[str, Any]:
        normalized_id = _document_id(document_id)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/detail",
            authorization=authorization,
            params={"documentType": "nfse", "branch": normalized_branch},
        )
        payload = _json_payload(response)
        if response.status_code >= 400 or payload.get("success") is False:
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível carregar os dados da NFS-e."),
                _mapped_status(response.status_code),
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise FinancialReceivedInvoiceGatewayError(
                "Os dados da NFS-e retornaram um formato inválido.",
                502,
            )
        return data

    def download_cte_xml(
        self,
        *,
        authorization: str,
        document_id: str,
        file_id: str,
        branch: str,
    ) -> tuple[bytes, str]:
        normalized_id = _document_id(document_id)
        normalized_file = _document_id(file_id)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/xml/original",
            authorization=authorization,
            params={
                "documentType": "cte",
                "fileId": normalized_file,
                "branch": normalized_branch,
            },
        )
        if response.status_code >= 400:
            payload = _json_payload(response)
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível obter o XML do CT-e."),
                _mapped_status(response.status_code),
            )
        content = response.content or b""
        if len(content) > _MAX_PDF_BYTES or not _looks_like_xml(content):
            raise FinancialReceivedInvoiceGatewayError("O XML do CT-e retornado é inválido.", 502)
        return content, f"CTe-{normalized_id}.xml"

    def download_dacte(
        self,
        *,
        authorization: str,
        document_id: str,
        file_id: str,
        access_key: str,
        branch: str,
    ) -> tuple[bytes, str]:
        normalized_id = _document_id(document_id)
        normalized_file = _document_id(file_id)
        normalized_key = _cte_access_key(access_key)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/dacte",
            authorization=authorization,
            params={
                "fileId": normalized_file,
                "accessKey": normalized_key,
                "branch": normalized_branch,
            },
        )
        if response.status_code >= 400:
            payload = _json_payload(response)
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível obter o DACTE."),
                _mapped_status(response.status_code),
            )
        content = response.content or b""
        if len(content) > _MAX_PDF_BYTES or not content.startswith(b"%PDF"):
            raise FinancialReceivedInvoiceGatewayError("O DACTE retornado não é um PDF válido.", 502)
        return content, f"CTe-{normalized_key}.pdf"

    def get_cte_detail(
        self,
        *,
        authorization: str,
        document_id: str,
        file_id: str,
        access_key: str,
        branch: str,
    ) -> dict[str, Any]:
        normalized_id = _document_id(document_id)
        normalized_file = _document_id(file_id)
        normalized_key = _cte_access_key(access_key)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/detail",
            authorization=authorization,
            params={
                "documentType": "cte",
                "fileId": normalized_file,
                "accessKey": normalized_key,
                "branch": normalized_branch,
            },
        )
        payload = _json_payload(response)
        if response.status_code >= 400 or payload.get("success") is False:
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível carregar os dados do CT-e."),
                _mapped_status(response.status_code),
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise FinancialReceivedInvoiceGatewayError(
                "Os dados do CT-e retornaram um formato inválido.",
                502,
            )
        return data

    def get_nfe_detail(
        self,
        *,
        authorization: str,
        document_id: str,
        provider_entity_id: str,
        access_key: str,
        branch: str,
    ) -> dict[str, Any]:
        normalized_id = _document_id(document_id)
        normalized_entity = _document_id(provider_entity_id)
        normalized_key = _nfe_access_key(access_key)
        normalized_branch = _branch(branch)
        response = self._get(
            f"/invoices/received/{quote(normalized_id, safe='')}/detail",
            authorization=authorization,
            params={
                "documentType": "nfe",
                "providerEntityId": normalized_entity,
                "accessKey": normalized_key,
                "branch": normalized_branch,
            },
        )
        payload = _json_payload(response)
        if response.status_code >= 400 or payload.get("success") is False:
            raise FinancialReceivedInvoiceGatewayError(
                _safe_message(payload, "Não foi possível carregar os dados da NF-e."),
                _mapped_status(response.status_code),
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise FinancialReceivedInvoiceGatewayError(
                "Os dados da NF-e retornaram um formato inválido.",
                502,
            )
        return data

    def _get(
        self,
        path: str,
        *,
        authorization: str,
        params: dict[str, str],
    ) -> httpx.Response:
        user_authorization = str(authorization or "").strip()
        if not user_authorization.lower().startswith("bearer "):
            raise FinancialReceivedInvoiceGatewayError("Sessão ausente para consultar as notas.", 401)
        headers = {
            "X-Delpi-Service-Token": self._require_service_token(),
            "Accept": "application/json, application/pdf, text/xml",
        }
        last_error: FinancialReceivedInvoiceGatewayError | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = self._send(path, headers=headers, params=params)
            except httpx.TimeoutException:
                last_error = FinancialReceivedInvoiceGatewayError(
                    "A consulta de notas fiscais demorou além do limite.",
                    503,
                )
            except httpx.HTTPError:
                last_error = FinancialReceivedInvoiceGatewayError(
                    "A consulta de notas fiscais está indisponível.",
                    503,
                )
            else:
                if response.status_code not in _TRANSIENT_STATUS or attempt == _MAX_ATTEMPTS:
                    return response
                self._sleep(_retry_delay(attempt, response))
                continue
            if attempt == _MAX_ATTEMPTS and last_error is not None:
                raise last_error
            self._sleep(_retry_delay(attempt, None))
        raise FinancialReceivedInvoiceGatewayError(
            "A consulta de notas fiscais está indisponível.",
            503,
        )

    def _require_service_token(self) -> str:
        if self._service_token is None:
            configured = get_internal_service_token()
        else:
            configured = self._service_token
        token = (configured or "").strip()
        if not token:
            raise FinancialReceivedInvoiceGatewayError(
                "A consulta de notas fiscais está indisponível.",
                503,
            )
        return token

    def _send(self, path: str, *, headers: dict[str, str], params: dict[str, str]) -> httpx.Response:
        timeout = _timeout(self._timeout_seconds)
        if self._client is not None:
            return self._client.get(
                f"{self._base_url}{path}",
                headers=headers,
                params=params,
                timeout=timeout,
            )
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            return client.get(
                f"{self._base_url}{path}",
                headers=headers,
                params=params,
            )


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


def _safe_message(payload: dict[str, Any], fallback: str) -> str:
    message = str(payload.get("message") or "").strip()
    lowered = message.lower()
    if (
        not message
        or "<" in message
        or "entrarcomtoken" in lowered
        or "token=" in lowered
        or "questorpublico" in lowered
    ):
        return fallback
    return message[:300]


def _mapped_status(status_code: int) -> int:
    if status_code in {401, 403, 404, 422, 502, 503}:
        return status_code
    if 400 <= status_code < 500:
        return 422
    return 502


def _document_id(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if len(normalized) != _DOCUMENT_ID_LENGTH or any(ch not in "0123456789abcdef" for ch in normalized):
        raise FinancialReceivedInvoiceGatewayError(
            "Identificador do documento fiscal inválido.",
            422,
        )
    return normalized


def _access_key(value: str) -> str:
    normalized = str(value or "").strip()
    if len(normalized) != _ACCESS_KEY_LENGTH or not normalized.isdigit():
        raise FinancialReceivedInvoiceGatewayError("Chave de acesso inválida.", 422)
    return normalized


def _cte_access_key(value: str) -> str:
    normalized = _access_key(value)
    if normalized[20:22] != "57":
        raise FinancialReceivedInvoiceGatewayError("Chave de acesso do CT-e inválida.", 422)
    return normalized


def _nfe_access_key(value: str) -> str:
    normalized = _access_key(value)
    if normalized[20:22] != "55":
        raise FinancialReceivedInvoiceGatewayError("Chave de acesso da NF-e inválida.", 422)
    return normalized


def _xml_variant(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized not in {"original", "standard"}:
        raise FinancialReceivedInvoiceGatewayError("Tipo de XML da NFS-e inválido.", 422)
    return normalized


def _looks_like_xml(content: bytes) -> bool:
    sample = _xml_inspection_sample(content)[:240].lower()
    if sample.startswith(b"<html") or sample.startswith(b"<!doctype") or sample.startswith(b"%pdf"):
        return False
    folded = content.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        return False
    return sample.startswith(b"<")


def _xml_inspection_sample(payload: bytes) -> bytes:
    sample = payload.lstrip(b" \t\r\n\x0b\x0c")
    for bom in (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"):
        if sample.startswith(bom):
            return sample[len(bom) :].lstrip(b" \t\r\n\x0b\x0c")
    return sample


def _branch(value: str) -> str:
    normalized = str(value or "").strip()
    if normalized not in _BRANCHES:
        raise FinancialReceivedInvoiceGatewayError("Filial de origem inválida.", 422)
    return normalized

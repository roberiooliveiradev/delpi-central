"""HTTP client — Product Drawing PDF owned by api-delpi."""

from __future__ import annotations

import re
from typing import Any

import httpx

from production_control_app.config import settings
from production_control_app.domain.errors import (
    DelpiGatewayError,
    DrawingNotFound,
    DrawingSourceUnavailable,
)
from production_control_app.domain.ports.drawing_library import DrawingLibraryPort
from production_control_app.domain.product_drawing_pdf import DrawingFile
from production_control_app.infrastructure.gateways.delpi_production_gateway import (
    bearer_authorization_from_context,
)

from delpi_auth.service_token import apply_internal_service_headers

_FILENAME_RE = re.compile(
    r"""filename\*=UTF-8''([^;]+)|filename="([^"]+)"|filename=([^;]+)""",
    re.IGNORECASE,
)
_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$", re.IGNORECASE)


class ApiDelpiDrawingLibraryClient(DrawingLibraryPort):
    """Resolve PDF via api-delpi ``GET /products/{code}/drawing/pdf``.

    Does not touch the FILESERVER. Auth uses the same BFF context as
    ``DelpiProductionGateway`` (end-user JWT when present, else internal service token).
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.DELPI_API_URL).rstrip("/")
        self._timeout = float(timeout or settings.DELPI_API_TIMEOUT)
        self._caller_app = caller_app or settings.DELPI_API_CALLER_APP

    def resolve_pdf(self, code: str) -> DrawingFile:
        normalized = self._normalize_code(code)
        url = f"{self._base_url}/products/{normalized}/drawing/pdf"
        headers = self._headers()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers)
        except httpx.RequestError as exc:
            raise DrawingSourceUnavailable(
                "Biblioteca de desenhos indisponível: falha ao consultar a api-delpi."
            ) from exc

        if response.status_code == 404:
            raise DrawingNotFound("Desenho não encontrado para este produto.")
        if response.status_code == 503:
            detail = self._message_from_body(response) or (
                "Biblioteca de desenhos indisponível: pasta não montada no servidor."
            )
            raise DrawingSourceUnavailable(detail)
        if response.status_code == 422:
            detail = self._message_from_body(response) or "Código do PA inválido para busca de desenho."
            raise DrawingNotFound(detail)
        if response.status_code >= 400:
            detail = self._message_from_body(response) or "Erro ao consultar desenho na api-delpi."
            raise DelpiGatewayError(detail, status_code=response.status_code)

        content = response.content or b""
        if not content.startswith(b"%PDF"):
            raise DrawingNotFound("Resposta de desenho inválida da api-delpi.")

        filename = self._filename_from_headers(response.headers, fallback=f"{normalized}.pdf")
        return DrawingFile(filename=filename, content=content, media_type="application/pdf")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/pdf",
            "X-Delpi-Caller-App": self._caller_app,
        }
        authorization = bearer_authorization_from_context()
        if authorization:
            headers["Authorization"] = authorization
        apply_internal_service_headers(headers)
        return headers

    @staticmethod
    def _normalize_code(code: str) -> str:
        normalized = str(code or "").strip().upper()
        if (
            not normalized
            or ".." in normalized
            or "/" in normalized
            or "\\" in normalized
            or not _CODE_PATTERN.fullmatch(normalized)
        ):
            raise DrawingNotFound("Código do PA inválido para busca de desenho.")
        return normalized

    @staticmethod
    def _message_from_body(response: httpx.Response) -> str | None:
        try:
            body: Any = response.json()
        except Exception:
            return None
        if not isinstance(body, dict):
            return None
        for key in ("message", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _filename_from_headers(headers: httpx.Headers, *, fallback: str) -> str:
        disposition = headers.get("content-disposition") or ""
        match = _FILENAME_RE.search(disposition)
        if not match:
            return fallback
        raw = next((g for g in match.groups() if g), None)
        if not raw:
            return fallback
        name = raw.strip().split("/")[-1].split("\\")[-1]
        if not name or ".." in name:
            return fallback
        return name

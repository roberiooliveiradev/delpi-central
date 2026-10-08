"""HTTP gateway — desenho PDF do produto via api-delpi (fonte canônica).

Resolve ``GET {DELPI_API_URL}/products/{code}/drawing/pdf`` com os mesmos
headers S2S do restante da integração (``apply_internal_service_headers`` +
``X-Delpi-Caller-App: requests-api``) e repasse do JWT do usuário quando
presente — a autorização efetiva fica na api-delpi. O token interno nunca vai
a log nem para o cliente.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from delpi_auth.request_context import get_request_authorization
from delpi_auth.service_token import apply_internal_service_headers

from requests_app.application.errors import ApplicationError
from requests_app.config import settings
from requests_app.domain.ports.product_drawing_port import (
    ProductDrawingFile,
    ProductDrawingGatewayPort,
)

_FILENAME_RE = re.compile(
    r"""filename\*=UTF-8''([^;]+)|filename="([^"]+)"|filename=([^;]+)""",
    re.IGNORECASE,
)
_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$", re.IGNORECASE)


def _invalid_code() -> ApplicationError:
    return ApplicationError(
        code="drawing_not_found",
        status_code=404,
        detail="Código do PA inválido para busca de desenho.",
    )


def normalize_drawing_code(code: str) -> str:
    normalized = str(code or "").strip().upper()
    if (
        not normalized
        or ".." in normalized
        or "/" in normalized
        or "\\" in normalized
        or not _CODE_PATTERN.fullmatch(normalized)
    ):
        raise _invalid_code()
    return normalized


class ApiDelpiProductDrawingGateway(ProductDrawingGatewayPort):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.DELPI_API_URL).rstrip("/")
        self._timeout = float(timeout or settings.DELPI_API_TIMEOUT or 30)
        self._caller_app = (
            caller_app or settings.DELPI_API_CALLER_APP or "requests-api"
        ).strip()

    def resolve_pdf(self, code: str) -> ProductDrawingFile:
        normalized = normalize_drawing_code(code)
        url = f"{self._base_url}/products/{normalized}/drawing/pdf"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx.RequestError as exc:
            raise ApplicationError(
                code="drawing_source_unavailable",
                status_code=503,
                detail="Não foi possível consultar o desenho neste momento.",
            ) from exc

        if response.status_code == 404:
            raise ApplicationError(
                code="drawing_not_found",
                status_code=404,
                detail="Desenho não encontrado para este produto.",
            )
        if response.status_code == 422:
            raise _invalid_code()
        if response.status_code == 503:
            raise ApplicationError(
                code="drawing_source_unavailable",
                status_code=503,
                detail="Não foi possível consultar o desenho neste momento.",
            )
        if response.status_code in {401, 403}:
            raise ApplicationError(
                code="drawing_upstream_unauthorized",
                status_code=502,
                detail="Não foi possível consultar o desenho neste momento.",
            )
        if response.status_code >= 400:
            raise ApplicationError(
                code="drawing_upstream_error",
                status_code=502,
                detail="Não foi possível consultar o desenho neste momento.",
            )

        content = response.content or b""
        if not content.startswith(b"%PDF"):
            raise ApplicationError(
                code="drawing_not_found",
                status_code=404,
                detail="Desenho não encontrado para este produto.",
            )
        filename = self._filename_from_headers(
            response.headers, fallback=f"{normalized}.pdf"
        )
        return ProductDrawingFile(filename=filename, content=content)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/pdf",
            "X-Delpi-Caller-App": self._caller_app,
        }
        authorization = str(get_request_authorization() or "").strip()
        if authorization:
            headers["Authorization"] = (
                authorization
                if authorization.lower().startswith("bearer ")
                else f"Bearer {authorization}"
            )
        apply_internal_service_headers(headers)
        return headers

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


class InMemoryProductDrawingGateway(ProductDrawingGatewayPort):
    """Test double — canned PDF por código, com falhas configuráveis."""

    def __init__(
        self,
        *,
        content: bytes = b"%PDF-1.4 fake",
        exc: ApplicationError | None = None,
    ) -> None:
        self.calls: list[str] = []
        self._content = content
        self._exc = exc

    def resolve_pdf(self, code: str) -> ProductDrawingFile:
        self.calls.append(str(code))
        if self._exc is not None:
            raise self._exc
        normalized = normalize_drawing_code(code)
        return ProductDrawingFile(
            filename=f"{normalized}.pdf", content=self._content
        )

from __future__ import annotations

import httpx
import pytest

from production_control_app.domain.errors import (
    DelpiGatewayError,
    DrawingNotFound,
    DrawingSourceUnavailable,
)
from production_control_app.infrastructure.gateways.api_delpi_drawing_library_client import (
    ApiDelpiDrawingLibraryClient,
)

_REAL_CLIENT = httpx.Client


class _FakeTransport(httpx.BaseTransport):
    def __init__(self, handler) -> None:
        self._handler = handler

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._handler(request)


def _patch_http(monkeypatch: pytest.MonkeyPatch, transport: httpx.BaseTransport) -> None:
    monkeypatch.setattr(
        "production_control_app.infrastructure.gateways.api_delpi_drawing_library_client.httpx.Client",
        lambda **kwargs: _REAL_CLIENT(transport=transport, **kwargs),
    )
    monkeypatch.setattr(
        "production_control_app.infrastructure.gateways.api_delpi_drawing_library_client.bearer_authorization_from_context",
        lambda: None,
    )
    monkeypatch.setattr(
        "production_control_app.infrastructure.gateways.api_delpi_drawing_library_client.apply_internal_service_headers",
        lambda headers: None,
    )


def test_resolve_pdf_returns_content_and_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = b"%PDF-1.4 fake-drawing"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/products/90262957/drawing/pdf"
        return httpx.Response(
            200,
            content=pdf,
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": 'inline; filename="90262957_R02.pdf"',
            },
            request=request,
        )

    _patch_http(monkeypatch, _FakeTransport(handler))
    drawing = ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("90262957")

    assert drawing.filename == "90262957_R02.pdf"
    assert drawing.content == pdf
    assert drawing.path is None
    assert drawing.media_type == "application/pdf"


def test_404_is_drawing_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"message": "Desenho não encontrado para este PA."},
            request=request,
        )

    _patch_http(monkeypatch, _FakeTransport(handler))
    with pytest.raises(DrawingNotFound, match="não encontrado"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("11111111")


def test_503_is_source_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"message": "Biblioteca de desenhos indisponível."},
            request=request,
        )

    _patch_http(monkeypatch, _FakeTransport(handler))
    with pytest.raises(DrawingSourceUnavailable, match="indisponível"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("90262957")


def test_network_error_is_source_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class BoomTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

    _patch_http(monkeypatch, BoomTransport())
    with pytest.raises(DrawingSourceUnavailable, match="falha ao consultar"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("90262957")


def test_rejects_path_traversal() -> None:
    with pytest.raises(DrawingNotFound, match="inválido"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("../etc/passwd")


@pytest.mark.parametrize(
    "code",
    ["", "90262957/x", "90262957\\x", "..90262957", "http://evil", "file://x"],
)
def test_rejects_unsafe_codes(code: str) -> None:
    with pytest.raises(DrawingNotFound, match="inválido"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf(code)


def test_auth_error_is_gateway_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"}, request=request)

    _patch_http(monkeypatch, _FakeTransport(handler))
    with pytest.raises(DelpiGatewayError, match="Unauthorized"):
        ApiDelpiDrawingLibraryClient(base_url="http://api-delpi.test").resolve_pdf("90262957")

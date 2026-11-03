"""EVA DEC-VAL-016 — exportação do PDF oficial via MCP (product.drawing_download).

read(product, drawing_download) entrega os bytes do desenho oficial como
EmbeddedResource (BlobResourceContents base64) dentro do tools/call —
mesma delegação governada das rotas REST, AuthZ fail-closed e estados
honestos tipados.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
from types import SimpleNamespace

import pytest
from mcp.types import EmbeddedResource, TextContent

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)

from engineering_app.interface.mcp import semantic_bridge as sem
from engineering_app.interface.mcp import tool_bridge as bridge

PDF_BYTES = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


def _human_user(permissions=("engineering.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


class _AuxStub:
    def __init__(self, result):
        self._result = result

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        return self._result


def _install(monkeypatch, result):
    stub = _AuxStub(result)
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: stub
    )
    return stub


def _available(filename="DES-90264302.pdf", content=PDF_BYTES):
    return {
        "status": "available",
        "status_code": 200,
        "content": content,
        "content_type": "application/pdf",
        "filename": filename,
    }


def _call(monkeypatch, result, ref="90264302"):
    _install(monkeypatch, result)
    _set_context(_human_user())
    return asyncio.run(
        sem.tool_read(
            entity="product", action="drawing_download", ref=ref
        )
    )


# --- transporte / contrato --------------------------------------------------


def test_drawing_download_returns_embedded_resource(monkeypatch):
    result = _call(monkeypatch, _available())
    assert not result.is_error
    payload = result.structured_content
    assert payload["entity"] == "product"
    assert payload["action"] == "drawing_download"
    assert payload["success"] is True
    data = payload["data"]
    assert data["product_code"] == "90264302"
    assert data["filename"] == "DES-90264302.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["size_bytes"] == len(PDF_BYTES)
    assert data["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert data["transport"] == "embedded_resource"

    kinds = [type(item).__name__ for item in result.content]
    assert "TextContent" in kinds
    assert "EmbeddedResource" in kinds
    embedded = next(
        item for item in result.content
        if isinstance(item, EmbeddedResource)
    )
    resource = embedded.resource
    assert resource.mime_type == "application/pdf"
    assert base64.b64decode(resource.blob) == PDF_BYTES
    assert str(resource.uri).endswith("DES-90264302.pdf")


def test_drawing_download_sanitizes_filename(monkeypatch):
    result = _call(
        monkeypatch,
        _available(filename='../../etc/\r\n"bad".pdf'),
    )
    assert not result.is_error
    embedded = next(
        item for item in result.content
        if isinstance(item, EmbeddedResource)
    )
    filename = result.structured_content["data"]["filename"]
    assert "\r" not in filename and '"' not in filename
    assert ".." not in filename
    assert str(embedded.resource.uri).endswith(filename)


def test_drawing_download_no_filename_falls_back_to_code(monkeypatch):
    result = _call(monkeypatch, _available(filename=None))
    data = result.structured_content["data"]
    assert data["filename"] == "90264302.pdf"


def test_get_context_advertises_drawing_download(monkeypatch):
    _set_context(_human_user())
    result = sem.tool_get_context(entity="product")
    assert not result.is_error
    actions = {
        a["action"] for a in result.structured_content["data"]["actions"]
    }
    assert "drawing_download" in actions
    assert "drawing" in actions


# --- AuthZ / estados honestos ------------------------------------------------


def test_drawing_download_requires_auth(monkeypatch):
    _install(monkeypatch, _available())
    result = asyncio.run(
        sem.tool_read(
            entity="product", action="drawing_download", ref="90264302"
        )
    )
    assert result.is_error


def test_drawing_download_denied_without_access(monkeypatch):
    _install(monkeypatch, _available())
    _set_context(_human_user(permissions=()))
    result = asyncio.run(
        sem.tool_read(
            entity="product", action="drawing_download", ref="90264302"
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_drawing_download_service_principal_denied(monkeypatch):
    _install(monkeypatch, _available())
    _set_context(
        _human_user(principal_type="service"), "Bearer svc-token"
    )
    result = asyncio.run(
        sem.tool_read(
            entity="product", action="drawing_download", ref="90264302"
        )
    )
    assert result.is_error


def test_drawing_download_forbidden_upstream(monkeypatch):
    result = _call(monkeypatch, {"status": "forbidden", "reason": "denied"})
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_drawing_download_not_found(monkeypatch):
    result = _call(monkeypatch, {"status": "not_found", "reason": "missing"})
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_drawing_download_unavailable(monkeypatch):
    result = _call(monkeypatch, {"status": "unavailable", "reason": "x"})
    assert result.is_error
    assert result.structured_content["status_code"] == 502


def test_drawing_download_requires_ref(monkeypatch):
    _install(monkeypatch, _available())
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(entity="product", action="drawing_download")
    )
    assert result.is_error
    assert "ref" in result.structured_content["message"]


# --- compatibilidade ----------------------------------------------------------


def test_existing_drawing_actions_unaffected(monkeypatch):
    """product.drawing (metadados) e product.structure seguem intactos."""

    class _MetaStub:
        async def fetch_product_drawing(self, ctx, *, code):
            return {"status": "available", "data": {"found": True}}

        async def fetch_product_structure(self, ctx, **kw):
            return {"status": "available", "data": {"children": []}}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _MetaStub()
    )
    _set_context(_human_user())
    meta = asyncio.run(
        sem.tool_read(entity="product", action="drawing", ref="90264302")
    )
    assert not meta.is_error
    assert not any(
        isinstance(item, EmbeddedResource) for item in meta.content
    )
    structure = asyncio.run(
        sem.tool_read(entity="product", action="structure", ref="90264302")
    )
    assert not structure.is_error


def test_wrap_preserves_non_text_content(monkeypatch):
    """Envelope semântico não descarta EmbeddedResource do handler."""
    result = _call(monkeypatch, _available())
    assert any(
        isinstance(item, EmbeddedResource) for item in result.content
    )
    text = next(
        item for item in result.content if isinstance(item, TextContent)
    )
    assert "drawing_download" in text.text

"""EVA #131 / DEC-VAL-014 — contrato binário do proxy de PDF do desenho.

Garantias: `Content-Disposition: attachment` fixo na resposta final (a
disposição upstream — inclusive `inline` — nunca é ecoada), filename
sanitizado contra header injection, integridade SHA-256/tamanho sobre os
bytes efetivamente entregues, OpenAPI declarando `application/pdf`
binário e AuthZ fail-closed inalterada.
"""

from __future__ import annotations

import hashlib

import engineering_app.interface.http.routes.product_routes as product_routes
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.delegated_auxiliary import (
    ApiDelpiDelegatedAuxiliary,
    _disposition_filename,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamError,
)

PDF_BYTES = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class _AuxStub:
    """Stub do source delegado — contrato pós-adapter."""

    def __init__(self, result):
        self._result = result

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        return self._result


def _install_stub(monkeypatch, result):
    stub = _AuxStub(result)
    monkeypatch.setattr(
        product_routes, "build_delegated_auxiliary_source", lambda: stub
    )
    return stub


def _available(filename=None, content=PDF_BYTES):
    return {
        "status": "available",
        "status_code": 200,
        "content": content,
        "content_type": "application/pdf",
        "filename": filename,
    }


class _RawClientStub:
    """Client downstream fake — controla headers/bytes do upstream."""

    def __init__(self, headers, content=PDF_BYTES):
        self._headers = headers
        self._content = content
        self.calls = []

    async def get_raw(
        self,
        path,
        *,
        params=None,
        access_token,
        request_id=None,
        service_token=None,
    ):
        self.calls.append(path)
        return 200, self._headers, self._content


def _install_upstream(monkeypatch, headers, content=PDF_BYTES):
    """Adapter real + client fake — exercita parse upstream → rota."""
    client_stub = _RawClientStub(headers, content)
    source = ApiDelpiDelegatedAuxiliary(client_stub)
    monkeypatch.setattr(
        product_routes, "build_delegated_auxiliary_source", lambda: source
    )
    return client_stub


# --- Attachment garantido -------------------------------------------------


def test_pdf_response_is_attachment_with_integrity(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available(filename="DES-0156-REV03.pdf"))
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert (
        resp.headers["content-disposition"]
        == 'attachment; filename="DES-0156-REV03.pdf"'
    )
    assert resp.content == PDF_BYTES
    assert resp.headers["x-document-sha256"] == hashlib.sha256(
        PDF_BYTES
    ).hexdigest()
    assert resp.headers["x-document-size"] == str(len(PDF_BYTES))
    assert resp.headers["x-document-filename"] == "DES-0156-REV03.pdf"
    assert resp.headers["x-document-product-code"] == "0156"


def test_upstream_inline_disposition_still_attachment(
    client, jwks_env, core_rbac, monkeypatch
):
    """DEC-VAL-014 §11.1 — api-delpi responde `inline; filename=...` via
    FileResponse; a borda deve emitir `attachment`, nunca ecoar `inline`."""
    _install_upstream(
        monkeypatch,
        {"content-disposition": 'inline; filename="DES-0156.pdf"'},
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 200
    disposition = resp.headers["content-disposition"]
    assert disposition == 'attachment; filename="DES-0156.pdf"'
    assert "inline" not in disposition


def test_upstream_attachment_disposition_stays_attachment(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_upstream(
        monkeypatch,
        {"content-disposition": 'attachment; filename="DES-0156.pdf"'},
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert (
        resp.headers["content-disposition"]
        == 'attachment; filename="DES-0156.pdf"'
    )


def test_upstream_without_disposition_falls_back_to_code(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_upstream(monkeypatch, {})
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert (
        resp.headers["content-disposition"]
        == 'attachment; filename="0156.pdf"'
    )
    assert resp.headers["x-document-filename"] == "0156.pdf"


def test_upstream_invalid_filename_is_sanitized(
    client, jwks_env, core_rbac, monkeypatch
):
    """Nome upstream com path/aspas/CRLF é reduzido a token seguro —
    nunca escapado dentro do header de saída."""
    _install_upstream(
        monkeypatch,
        {
            "content-disposition": 'inline; filename="../../etc/\r\n'
            'injected"name.pdf"'
        },
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    disposition = resp.headers["content-disposition"]
    assert disposition.startswith("attachment; filename=")
    assert "\r" not in disposition and "\n" not in disposition
    assert '"' not in disposition.split("filename=", 1)[1].strip('"')
    assert ".." not in disposition


# --- Adapter: parse do filename upstream ----------------------------------


def test_disposition_filename_parses_quoted():
    assert (
        _disposition_filename('inline; filename="DES-0156.pdf"')
        == "DES-0156.pdf"
    )


def test_disposition_filename_parses_rfc2231():
    assert (
        _disposition_filename(
            "attachment; filename*=utf-8''Desenho%20Final.pdf"
        )
        == "Desenho Final.pdf"
    )


def test_disposition_filename_absent():
    assert _disposition_filename(None) is None
    assert _disposition_filename("") is None
    assert _disposition_filename("inline") is None


async def test_adapter_maps_upstream_errors():
    class _ErrClient:
        def __init__(self, exc):
            self._exc = exc

        async def get_raw(self, path, **kw):
            raise self._exc

    ctx = HomeSourceContext(
        user_id="u1", access_token="t", request_id="r1"
    )
    forbidden = await ApiDelpiDelegatedAuxiliary(
        _ErrClient(DownstreamError("http", "denied", status_code=403))
    ).fetch_product_drawing_pdf(ctx, code="0156")
    assert forbidden["status"] == "forbidden"

    not_found = await ApiDelpiDelegatedAuxiliary(
        _ErrClient(DownstreamError("http", "missing", status_code=404))
    ).fetch_product_drawing_pdf(ctx, code="0156")
    assert not_found["status"] == "not_found"

    unavailable = await ApiDelpiDelegatedAuxiliary(
        _ErrClient(DownstreamError("timeout", "slow upstream"))
    ).fetch_product_drawing_pdf(ctx, code="0156")
    assert unavailable["status"] == "unavailable"


# --- Helper: filename seguro ------------------------------------------------


def test_attachment_filename_fallback_and_edges():
    fn = product_routes._attachment_filename
    assert fn(None, fallback="0156") == "0156.pdf"
    assert fn("  ", fallback="0156") == "0156.pdf"
    assert fn("../../etc/passwd", fallback="0156") == "passwd.pdf"
    assert fn("sem ext", fallback="0156") == "sem_ext.pdf"
    assert fn("RELATÓRIO Final.PDF", fallback="0156") == "RELAT_RIO_Final.PDF"
    assert fn("", fallback="0156") == "0156.pdf"


# --- Estados honestos / AuthZ ----------------------------------------------


def test_pdf_requires_auth(client):
    assert client.get("/v1/products/0156/drawing/pdf").status_code == 401


def test_pdf_denied_without_engineering_access(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available(filename="X.pdf"))
    core_rbac["behavior"] = ("data", rbac_payload_local([]))
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 403


def test_pdf_forbidden_source_maps_403(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, {"status": "forbidden", "reason": "denied"})
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 403


def test_pdf_not_found_maps_404(client, jwks_env, core_rbac, monkeypatch):
    _install_stub(monkeypatch, {"status": "not_found", "reason": "missing"})
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 404


def test_pdf_unavailable_maps_502(client, jwks_env, core_rbac, monkeypatch):
    _install_stub(monkeypatch, {"status": "unavailable", "reason": "timeout"})
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/0156/drawing/pdf", headers=_bearer(token)
    )
    assert resp.status_code == 502


# --- OpenAPI ----------------------------------------------------------------


def test_openapi_declares_binary_pdf_response(client):
    spec = client.get("/openapi.json").json()
    op = spec["paths"]["/v1/products/{product_code}/drawing/pdf"]["get"]
    assert op["operationId"] == "get_product_drawing_pdf"
    content = op["responses"]["200"]["content"]
    assert "application/pdf" in content
    assert "application/json" not in content
    assert content["application/pdf"]["schema"] == {
        "type": "string",
        "format": "binary",
    }


def rbac_payload_local(permissions, **overrides) -> dict:
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "roles": [],
        "groups": [],
        "permissions": list(permissions),
        "is_superadmin": False,
    }
    data.update(overrides)
    return data
